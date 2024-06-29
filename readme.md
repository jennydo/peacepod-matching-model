Thanh's note:

To be able to run python repo locally

**Create a virtual environment:**
This is the recommended approach. It isolates your project dependencies from the system Python.

```
python3 -m venv env
source env/bin/activate
```

After activating the virtual environment, your terminal prompt should change to indicate that the virtual environment is active.

**Install packages in the virtual environment:**
Once the virtual environment is activated, you can install packages without the externally-managed-environment error:

```
pip install pymongo Flask pandas scikit-learn
```

Start to run repo

```
python3 main.py
```
