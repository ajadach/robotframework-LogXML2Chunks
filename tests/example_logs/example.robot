*** Settings ***
Documentation       Example suite level documentation.
...
...
...                 *Steps*
...                 - Example Test 1
...                 - Example Test 2
...                 - Example Test 3
...                 - Example Test 4
...
...                 *Expected*
...                 - All test cases should be successful.

*** Test Cases ***
Example Test 1
    [Documentation]    Example Test 1 Documentation
    ...
    ...    *Steps / Expected*
    ...    - Log to HTML / pass
    ...
    ...    *Expected*
    ...    - Log should be successful.
    [Tags]    test_1
    log    Executing Example Test 1

Example Test 2
    [Documentation]    Example Test 1 Documentation
    ...
    ...    *Steps / Expected*
    ...    - Log to HTML / pass
    ...
    ...    *Expected*
    ...    - Log should be successful.
    [Tags]    test_2
    log    Executing Example Test 2

Example Test 3
    [Documentation]    Example Test 1 Documentation
    ...
    ...    *Steps / Expected*
    ...    - Log to HTML / pass
    ...
    ...    *Expected*
    ...    - Log should be successful.
    [Tags]    test_3
    log    Executing Example Test 3    

Example Test 4
    [Documentation]    Example Test 1 Documentation
    ...
    ...    *Steps / Expected*
    ...    - Log to HTML / pass
    ...
    ...    *Expected*
    ...    - Log should be successful.
    [Tags]    test_4
    log    Executing Example Test 4
