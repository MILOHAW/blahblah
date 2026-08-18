param()

Write-Host "Unlocking all Book of Monsters entries..."

$jsonPath = "e:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players\Nextstars.json"
$islandDbPath = "e:\Next-Private-Server-main\Captures\1\msm_json\24_db_island_v2.json"

$json = Get-Content $jsonPath | ConvertFrom-Json
$islandDb = Get-Content $islandDbPath | ConvertFrom-Json

# For island 1 specifically (Plant Island), add all its defined monsters
$dbIsland1 = $islandDb.payload.islands_data[0]
$dbMonsterIds = @($dbIsland1.monsters | ForEach-Object { $_.monster })

# Add to player's first island
$playerIsland = $json.player_object.islands[0]

if (-not $playerIsland.monsters) {
    $playerIsland | Add-Member -NotePropertyName "monsters" -NotePropertyValue @()
}

$existingIds = @($playerIsland.monsters | ForEach-Object { $_.monster })
Write-Host "Island 1: Player has $($existingIds.Count) monsters, database defines $($dbMonsterIds.Count)"

$addedCount = 0
foreach ($mId in $dbMonsterIds) {
    if ($existingIds -notcontains $mId) {
        $newMonster = $sampleMonster | ConvertTo-Json | ConvertFrom-Json
        $newMonster.monster = $mId
        $newMonster.island = $playerIsland.user_island_id
        $playerIsland.monsters += $newMonster
        $addedCount++
    }
}

Write-Host "Added $addedCount monsters to island 1"

$json | ConvertTo-Json -Depth 100 | Set-Content $jsonPath
Write-Host "Saved! All Book of Monsters entries should now be unlocked"
