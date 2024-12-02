# Adding a New Autocheck

This document outlines the steps to add a new autocheck to the codebase.

## Steps

### 1. Update Application Form

In `doaj/portality/forms/application_forms.py`, add `autocheck` to the `widgets` in the `admin` context for the required
field.

```python
# Example change in application_forms.py
"contexts": {
    "admin": {
        "widgets": [
            "autocheck",  # ~~^-> Autocheck:FormWidget~~
        ]
    }
}
```

### 2. Create the Checker Class

In doaj/portality/autocheck/checkers/, create a new file (e.g., new_autocheck.py). Add a class NewAutocheck that
inherits from Checker. Define `__identity__` as a unique identifier (e.g., `new_autocheck`) and implement the check
method
with the checker logic.

```python
# Example checker class in new_autocheck.py
class NewAutocheck(Checker):
    __identity__ = "new_autocheck"

    def check(self):
        # Add checker logic
        autochecks.add_check(
            field="application_field",  # Specifies the application field that the checker validates
            advice=self.MESSAGE,  # Message to add under the field
            checked_by=self.__identity__  # This attribute is required to use your checker's renderer
                                            # rather than the default one
        )

```

### 3. Register the Checker

In `doaj/portality/bll/services/autochecks.py`, add the new checker to the `AUTOCHECK_PLUGINS`.

### 4. Update JavaScript for the Checker

In `doaj/portality/static/js/autochecks.js`, update the `doaj.autocheckers.registry`
and create the checker's renderer `doaj.autocheckers.NewChecker` with `draw(autocheck)` method

### 5. Add the Checker to TestDrive

In `doaj/doajtest/testdrive/autocheck.py`, add the new checker to `autocheck_plugins`:

```python
acSvc = DOAJ.autochecksService(
    autocheck_plugins=[
        # (journal, application, plugin)
        (True, True, NewChecker)
    ]
)
```