import msm_handlers
import msm_store


def test_login_bootstrap_keeps_welcome_and_uses_captured_session_data():
    frames = msm_handlers.handle_login({})
    assert any(command == "gs_display_generic_message" for command, _ in frames)
    assert any(command == "game_settings" for command, _ in frames)
    assert any(command == "gs_initialized" for command, _ in frames)


def test_local_workspace_db_and_player_paths_are_discoverable():
    db_paths = [str(path) for path in msm_store._candidate_db_dirs()]
    player_paths = [str(path) for path in msm_store._candidate_players_dirs()]
    assert any("D:\\ZewicMsMPc\\Data\\db_files".lower() in p.lower() for p in db_paths)
    assert any("D:\\ZewicMsMPc\\My Singing Monsters Server\\SFS2X\\extensions\\MSM\\players".lower() in p.lower() for p in player_paths)
