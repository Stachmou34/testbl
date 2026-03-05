<?php
session_start();

// Initialisation des paramètres
$client_id = '910e4df6c413165168a3e7217272a17c';
$client_secret = '962ff3e49de24d0e26f550f8fa82c7f42f16cb855a5eb9c57ea9383887cbb206';
$redirect_uri = 'https://avaliberty.com/callback.php';  // URL de redirection
$token_url = 'https://myanimelist.net/v1/oauth2/token';

// Vérifier que le code d'autorisation est passé dans l'URL
if (isset($_GET['code'])) {
    echo "Code d'autorisation reçu: " . htmlspecialchars($_GET['code']) . "<br>";
} else {
    echo "Erreur: Code d'autorisation manquant.<br>";
}

// Vérifier que le code d'autorisation et le code verifier sont présents en session
if (isset($_GET['code']) && isset($_SESSION['code_verifier'])) {
    $authorization_code = $_GET['code'];
    $code_verifier = $_SESSION['code_verifier'];

    // Debug : Afficher le code verifier en session
    echo "Code Verifier en session: " . htmlspecialchars($code_verifier) . "<br>";

    // Préparer les données pour l'échange du code d'autorisation contre un jeton d'accès
    $post_data = [
        'client_id' => $client_id,
        'client_secret' => $client_secret,
        'grant_type' => 'authorization_code',
        'code' => $authorization_code,
        'redirect_uri' => $redirect_uri,
        'code_verifier' => $code_verifier
    ];

    // Debug : Afficher les données de la requête
    echo "Données envoyées pour obtenir le jeton d'accès: <br>";
    echo "<pre>";
    print_r($post_data);
    echo "</pre>";

    // Utiliser cURL pour envoyer la requête POST pour obtenir le jeton
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $token_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($post_data));

    // Obtenir la réponse
    $response = curl_exec($ch);

    // Vérifier si la requête a échoué
    if (curl_errno($ch)) {
        echo 'Erreur cURL: ' . curl_error($ch);
    }

    curl_close($ch);

    // Décoder la réponse JSON
    $response_data = json_decode($response, true);

    // Debug : Afficher la réponse de l'API
    echo "Réponse de l'API: <br>";
    echo "<pre>";
    print_r($response_data);
    echo "</pre>";

    // Vérifier si le jeton d'accès est dans la réponse
    if (isset($response_data['access_token'])) {
        echo "Jeton d'accès obtenu: " . $response_data['access_token'];
    } else {
        echo "Erreur: " . $response_data['error_description'];
    }
} else {
    echo "Erreur: Code d'autorisation manquant ou code verifier non valide.";
}
?>
