<?php
/**
 * Plugin Name: EVA iCal Importer für The Events Calendar
 * Description: Importiert den Elbe-Valley-Veranstaltungsfeed (.ics) täglich automatisch
 *              in "The Events Calendar". Kostenlose Alternative zum Event Aggregator.
 * Version: 1.0.0
 * Author: Elbe Valley Agentur
 *
 * Einrichtung:
 *   1. Als ZIP dieser Datei über Plugins → Installieren → Plugin hochladen einspielen
 *      und aktivieren (oder die Datei nach wp-content/mu-plugins/ kopieren).
 *   2. Unter Einstellungen → "EVA iCal Import" die Feed-URL eintragen und speichern.
 *      (Alternativ per Konstante EVA_ICS_FEED_URL in wp-config.php.)
 *   3. Fertig. Der Import läuft täglich via WP-Cron. "Jetzt importieren"-Button
 *      auf der Einstellungsseite für einen sofortigen Testlauf.
 *
 * Hinweis: Termine werden über ihre UID wiedererkannt (Meta _eva_ics_uid) und
 * aktualisiert statt doppelt angelegt. Entfernte Termine werden nicht gelöscht
 * (konservativ); das lässt sich bei Bedarf ergänzen.
 */

if (!defined('ABSPATH')) {
    exit;
}

const EVA_ICS_CRON_HOOK = 'eva_ics_import_event';
const EVA_ICS_UID_META  = '_eva_ics_uid';
const EVA_ICS_OPTION    = 'eva_ics_feed_url';

/** Feed-URL: Einstellungsseite (Option) hat Vorrang, sonst Konstante. */
function eva_ics_feed_url() {
    $opt = trim((string) get_option(EVA_ICS_OPTION, ''));
    if ($opt !== '') {
        return $opt;
    }
    return defined('EVA_ICS_FEED_URL') ? EVA_ICS_FEED_URL : '';
}

/* -------- Zeitplan (WP-Cron, täglich) -------- */

register_activation_hook(__FILE__, function () {
    if (!wp_next_scheduled(EVA_ICS_CRON_HOOK)) {
        wp_schedule_event(time() + 60, 'daily', EVA_ICS_CRON_HOOK);
    }
});
register_deactivation_hook(__FILE__, function () {
    wp_clear_scheduled_hook(EVA_ICS_CRON_HOOK);
});
// Falls als mu-plugin genutzt (keine Aktivierung): Zeitplan sicherstellen.
add_action('init', function () {
    if (!wp_next_scheduled(EVA_ICS_CRON_HOOK)) {
        wp_schedule_event(time() + 60, 'daily', EVA_ICS_CRON_HOOK);
    }
});

add_action(EVA_ICS_CRON_HOOK, 'eva_ics_run_import');

/* -------- Einstellungsseite (Einstellungen → EVA iCal Import) -------- */

add_action('admin_menu', function () {
    add_options_page(
        'EVA iCal Import',
        'EVA iCal Import',
        'manage_options',
        'eva-ics-import',
        'eva_ics_settings_page'
    );
});

add_action('admin_init', function () {
    register_setting('eva_ics_group', EVA_ICS_OPTION, array(
        'type' => 'string',
        'sanitize_callback' => 'esc_url_raw',
        'default' => '',
    ));
});

function eva_ics_settings_page() {
    if (!current_user_can('manage_options')) {
        return;
    }
    // Manueller Import per Button
    $notice = '';
    if (isset($_POST['eva_ics_run']) && check_admin_referer('eva_ics_run_now')) {
        $count = eva_ics_run_import();
        $notice = 'Import ausgeführt. Verarbeitete Termine: ' . intval($count);
    }
    $url = esc_attr(get_option(EVA_ICS_OPTION, ''));
    ?>
    <div class="wrap">
      <h1>EVA iCal Import</h1>
      <?php if ($notice): ?><div class="notice notice-success"><p><?php echo esc_html($notice); ?></p></div><?php endif; ?>
      <form method="post" action="options.php">
        <?php settings_fields('eva_ics_group'); ?>
        <table class="form-table">
          <tr>
            <th scope="row"><label for="eva_ics_url">Feed-URL (.ics)</label></th>
            <td>
              <input name="<?php echo esc_attr(EVA_ICS_OPTION); ?>" id="eva_ics_url"
                     type="url" class="regular-text" value="<?php echo $url; ?>"
                     placeholder="https://<org>.github.io/<repo>/elbe-valley-events.ics">
              <p class="description">Die von GitHub Pages veröffentlichte Kalenderdatei.</p>
            </td>
          </tr>
        </table>
        <?php submit_button('Speichern'); ?>
      </form>
      <hr>
      <form method="post">
        <?php wp_nonce_field('eva_ics_run_now'); ?>
        <input type="hidden" name="eva_ics_run" value="1">
        <?php submit_button('Jetzt importieren', 'secondary'); ?>
      </form>
    </div>
    <?php
}

/* -------- Hauptlogik -------- */

function eva_ics_run_import() {
    if (!function_exists('tribe_create_event')) {
        error_log('EVA iCal Importer: The Events Calendar ist nicht aktiv.');
        return 0;
    }
    $url = eva_ics_feed_url();
    if (!$url) {
        error_log('EVA iCal Importer: Feed-URL ist nicht gesetzt (Einstellungen → EVA iCal Import).');
        return 0;
    }

    $response = wp_remote_get($url, array('timeout' => 30));
    if (is_wp_error($response) || wp_remote_retrieve_response_code($response) !== 200) {
        error_log('EVA iCal Importer: Feed konnte nicht geladen werden.');
        return 0;
    }

    $events = eva_ics_parse(wp_remote_retrieve_body($response));
    $count = 0;
    foreach ($events as $ev) {
        eva_ics_upsert_event($ev);
        $count++;
    }
    return $count;
}

/**
 * Minimaler iCalendar-Parser: liefert Array von Events mit
 * uid, title, start, end, description, location, url.
 */
function eva_ics_parse($ics) {
    // Zeilen entfalten (RFC 5545: Fortsetzungszeilen beginnen mit Space/Tab).
    $ics = preg_replace("/\r\n[ \t]/", '', $ics);
    $ics = str_replace("\r\n", "\n", $ics);

    $events = array();
    if (!preg_match_all('/BEGIN:VEVENT(.*?)END:VEVENT/s', $ics, $matches)) {
        return $events;
    }
    foreach ($matches[1] as $block) {
        $ev = array(
            'uid' => '', 'title' => '', 'start' => '', 'end' => '',
            'description' => '', 'location' => '', 'url' => '',
        );
        foreach (explode("\n", $block) as $line) {
            $line = trim($line);
            if ($line === '') {
                continue;
            }
            $sep = strpos($line, ':');
            if ($sep === false) {
                continue;
            }
            $key = substr($line, 0, $sep);        // z.B. DTSTART;TZID=Europe/Berlin
            $val = substr($line, $sep + 1);
            $name = strtoupper(explode(';', $key)[0]);

            switch ($name) {
                case 'UID':         $ev['uid'] = $val; break;
                case 'SUMMARY':     $ev['title'] = eva_ics_unescape($val); break;
                case 'DESCRIPTION': $ev['description'] = eva_ics_unescape($val); break;
                case 'LOCATION':    $ev['location'] = eva_ics_unescape($val); break;
                case 'URL':         $ev['url'] = $val; break;
                case 'DTSTART':     $ev['start'] = eva_ics_to_datetime($val); break;
                case 'DTEND':       $ev['end'] = eva_ics_to_datetime($val); break;
            }
        }
        if ($ev['title'] && $ev['start']) {
            $events[] = $ev;
        }
    }
    return $events;
}

function eva_ics_unescape($v) {
    return str_replace(array('\\n', '\\,', '\\;', '\\\\'), array("\n", ',', ';', '\\'), $v);
}

/** '20260720T130000' oder '20260720' -> 'Y-m-d H:i:s' (lokale Zeit). */
function eva_ics_to_datetime($v) {
    $v = trim($v);
    if (preg_match('/(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})/', $v, $m)) {
        return "$m[1]-$m[2]-$m[3] $m[4]:$m[5]:$m[6]";
    }
    if (preg_match('/(\d{4})(\d{2})(\d{2})/', $v, $m)) {
        return "$m[1]-$m[2]-$m[3] 00:00:00";
    }
    return '';
}

/** Termin über UID wiederfinden und aktualisieren, sonst neu anlegen. */
function eva_ics_upsert_event($ev) {
    $existing = get_posts(array(
        'post_type'   => 'tribe_events',
        'post_status' => 'any',
        'numberposts' => 1,
        'meta_key'    => EVA_ICS_UID_META,
        'meta_value'  => $ev['uid'],
        'fields'      => 'ids',
    ));

    $description = $ev['description'];
    if ($ev['location']) {
        $description .= "\n\nOrt: " . $ev['location'];
    }
    if ($ev['url']) {
        $description .= "\n" . $ev['url'];
    }

    $args = array(
        'post_title'   => $ev['title'],
        'post_content' => trim($description),
        'post_status'  => 'publish',
        'EventStartDate' => date('Y-m-d', strtotime($ev['start'])),
        'EventStartTime' => date('H:i:s', strtotime($ev['start'])),
        'EventEndDate'   => date('Y-m-d', strtotime($ev['end'] ?: $ev['start'])),
        'EventEndTime'   => date('H:i:s', strtotime($ev['end'] ?: $ev['start'])),
        'EventURL'       => $ev['url'],
    );

    if (!empty($existing)) {
        $args['ID'] = $existing[0];
        tribe_update_event($existing[0], $args);
        $post_id = $existing[0];
    } else {
        $post_id = tribe_create_event($args);
        if ($post_id) {
            update_post_meta($post_id, EVA_ICS_UID_META, $ev['uid']);
        }
    }
    return $post_id;
}
