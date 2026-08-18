param()

$jsonPath = "e:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players\Nextstars.json"
$json = Get-Content $jsonPath | ConvertFrom-Json

# Set book_value for ALL monsters on island 1
$island = $json.player_object.islands[0]
$updated = 0

if ($island.monsters) {
    foreach ($monster in $island.monsters) {
        # Make sure book_value exists and is set to a non-zero value  
        if (-not $monster.PSObject.Properties['book_value']) {
            $monster | Add-Member -NotePropertyName "book_value" -NotePropertyValue 0
        }
        # If book_value is 0 or missing, set it to 16000 (like original monsters)
        if ($monster.book_value -eq $null -or $monster.book_value -eq 0) {
            $monster.book_value = 16000
            $updated++
        }
    }
}

Write-Host "Set book_value for $updated monsters"

$json | ConvertTo-Json -Depth 100 | Set-Content $jsonPath
Write-Host "Saved!"
