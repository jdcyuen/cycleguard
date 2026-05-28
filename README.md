
E:\CycleGuard

Github repository
https://github.com/jdcyuen/cycleguard.git

If you are just running the code locally on your machine, you don't have to do anything. It will automatically default to dev and use dev.yaml.

If you want to run your tests, your test suite (or you) can set the environment variable right before running the code so it uses test.yaml:

powershell
-----------
$env:CYCLEGUARD_ENV="test"
pytest

If you are deploying to production, you would configure your server/host to have the environment variable set to prod, and it will automatically switch to using prod.yaml.


How to run:

    cd E:\CycleGuard
    python scripts\daily_rebalance.py
or
	streamlit run src/dashboard/cycleguard_dashboard.py


#Run tests via:
python -m unittest tests/test_crash_manager.py















