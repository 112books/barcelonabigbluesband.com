<?php
/**
 * Handler dels formularis de contacte i contractació — Barcelona Big Blues Band
 * Desplegat a vl28359.dinaserver.com → https://barcelonabigbluesband.com/send-booking.php
 *
 * El camp ocult "form_type" decideix l'assumpte (booking | contact).
 * Requereix PHP 7.4+. Sense dependències externes.
 */

declare(strict_types=1);

const DEST_EMAIL = 'linuxbcn@gmail.com';
const FORM_LABELS = [
    'booking' => '[Contractació web barcelonabigbluesband.com]',
    'contact' => '[Contacte web barcelonabigbluesband.com]',
];
const RATE_LIMIT  = 10;          // peticions per IP...
const RATE_WINDOW = 3600;        // per aquesta finestra (segons)

// ── CORS: permetre el web de staging (GitHub Pages) i el domini de producció ──
$allowed = [
    'https://112books.github.io',
    'https://barcelonabigbluesband.com',
    'https://www.barcelonabigbluesband.com',
];
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $allowed, true)) {
    header('Access-Control-Allow-Origin: ' . $origin);
    header('Vary: Origin');
}
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'method_not_allowed']);
    exit;
}

// ── Honeypot: camp ocult que els bots omplen ──
if (!empty($_POST['_hp'])) {
    echo json_encode(['ok' => true]);   // fingim èxit: no als bots
    exit;
}

// ── Limitació bàsica per IP (fitxer temporal) ──
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$dir = sys_get_temp_dir() . '/bbbb_booking_' . md5($ip);
$now = time();
$hits = array_filter(explode("\n", (string)@file_get_contents($dir)), function ($l) use ($now) {
    return (int)$l > $now - RATE_WINDOW;
});
if (count($hits) >= RATE_LIMIT) {
    http_response_code(429);
    echo json_encode(['ok' => false, 'error' => 'rate_limited']);
    exit;
}
$hits[] = (string)$now;
@file_put_contents($dir, implode("\n", $hits), LOCK_EX);

// ── Validació ──
// Nota: retirem CR/LF de tots els camps per evitar injecció de capçaleres a mail().
$form    = ($_POST['form_type'] ?? 'booking') === 'contact' ? 'contact' : 'booking';
$name    = trim(str_replace(["\r", "\n"], '', (string)($_POST['name'] ?? '')));
$email   = trim(str_replace(["\r", "\n"], '', (string)($_POST['email'] ?? '')));
$org     = trim((string)($_POST['organisation'] ?? ''));
$date    = trim((string)($_POST['date'] ?? ''));
$message = trim((string)($_POST['message'] ?? ''));

$errors = [];
if ($name === '' || mb_strlen($name) > 120)           $errors[] = 'name';
if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) $errors[] = 'email';
if (mb_strlen($message) < 10 || mb_strlen($message) > 5000)      $errors[] = 'message';
if ($org !== '' && mb_strlen($org) > 200)             $errors[] = 'organisation';
if ($date !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $date)) $errors[] = 'date';

if ($errors) {
    http_response_code(422);
    echo json_encode(['ok' => false, 'error' => 'invalid_fields', 'fields' => $errors]);
    exit;
}

// ── Cos del correu ──
$body  = "Nou missatge des del formulari de " . ($form === 'contact' ? 'contacte' : 'contractació') . " del web\n";
$body .= str_repeat('-', 50) . "\n\n";
$body .= "Nom:           {$name}\n";
$body .= "Correu:        {$email}\n";
if ($form === 'booking') {
    $body .= "Organització:  " . ($org ?: '-') . "\n";
    $body .= "Data prevista: " . ($date ?: '-') . "\n";
}
$body .= "IP:            {$ip}\n\n";
$body .= "Missatge:\n{$message}\n";

$headers = [
    'From'         => 'noreply@barcelonabigbluesband.com',
    'Reply-To'     => $email,
    'Content-Type' => 'text/plain; charset=utf-8',
    'X-Mailer'     => 'PHP/' . PHP_VERSION,
];

$sent = mail(DEST_EMAIL, FORM_LABELS[$form] . ' ' . $name, $body, $headers);

if ($sent) {
    echo json_encode(['ok' => true]);
} else {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'send_failed']);
}
