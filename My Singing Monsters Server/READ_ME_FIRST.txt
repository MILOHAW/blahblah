NPS SERVER - SAVE FIX + 97% CRASH CHECKER
=========================================

TWO STEPS. Both go in your server folder (the one with Config.json in it,
normally "My Singing Monsters Server").


STEP 1 - install the save fix

    Copy these three files into the server folder, replacing what is there:

        msm_handlers.py
        msm_store.py
        bridge_core.py

    They fix four things: every account was being served as "Nextstars" and
    shared one save file, logging in wiped every island and saved, disconnecting
    overwrote the save with an old snapshot, and saves were written in a way that
    could truncate.


STEP 2 - run the checker

    Put CHECK_AND_FIX.bat and timemsm_check.py in the same folder and
    double-click CHECK_AND_FIX.bat.

    It finds Python by itself (it looks in your .venv first, then the system
    one), then:

      - confirms the three files above are actually installed
      - finds any file in the players folder that is NOT a player save and moves
        it out of the way. A raw capture frame sitting there loads as a player
        with no data at all, and the client dies at exactly 97 percent.
      - renames stale session_* folders to _disabled_session_* so nothing can
        restore an old snapshot over live progress
      - compares your save against a real capture from the official servers and
        lists any field that does not belong, is the wrong type, or is too large
      - writes REPORT.txt

    It never deletes anything. Everything it moves is listed at the end of the
    report, so you can move it back.

    Safe to run more than once.


AFTER THAT

    Start the server and log in. If it still crashes at 97 percent, send back
    REPORT.txt and the server log, and the exact field can be identified from
    those.
