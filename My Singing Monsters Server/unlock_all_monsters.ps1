param()

$jsonPath = "e:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players\Nextstars.json"
$json = Get-Content $jsonPath | ConvertFrom-Json

Write-Host "Loading all monsters from database..."
$allMonsterIds = @()

$monsterFiles = @(Get-ChildItem "e:\Next-Private-Server-main\Captures\1\msm_json\*_db_monster.json" | Select-Object -ExpandProperty FullName)
Write-Host "Found $($monsterFiles.Count) monster database files"

# Load all unique monster IDs
foreach ($file in $monsterFiles) {
    $data = Get-Content $file | ConvertFrom-Json
    foreach ($m in $data.payload.monsters_data) {
        $allMonsterIds += $m.monster_id
    }
}

$uniqueMonsterIds = @($allMonsterIds | Sort-Object -Unique)
Write-Host "Total unique monsters: $($uniqueMonsterIds.Count)"

# Get a sample monster to clone from
$sampleMonster = $json.player_object.islands[0].monsters[0]

# For each island, make sure it has examples of all the monsters
foreach ($island in $json.player_object.islands) {
    if (-not $island.monsters) {
        $island | Add-Member -NotePropertyName "monsters" -NotePropertyValue @()
    }
    
    $existingIds = @($island.monsters | ForEach-Object { $_.monster })
    $addedCount = 0
    
    foreach ($mId in $uniqueMonsterIds) {
        if ($existingIds -notcontains $mId) {
            # Clone the sample and modify
            $newMonster = $sampleMonster | ConvertTo-Json | ConvertFrom-Json
            $newMonster.monster = $mId
            $newMonster.island = $island.user_island_id
            $newMonster.level = 1
            $newMonster.book_value = 0
            $island.monsters += $newMonster
            $addedCount++
        }
    }
    
    if ($addedCount -gt 0) {
        Write-Host "Island $($island.user_island_id): Added $addedCount monsters (now $($island.monsters.Count) total)"
    }
}

$json | ConvertTo-Json -Depth 100 | Set-Content $jsonPath
Write-Host "Saved! All islands now have all monsters"


