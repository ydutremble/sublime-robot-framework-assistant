*** Settings ***
Library           Selenium2Library
Documentation     foobar
Resource          simple_resrouce2.robot

*** Variable ***
${VAR2}            1

*** Test Cases ***
Example Test
    Log    ${True}
    ${some_var} =    Set Variable    12345

*** Keywords ***
My Kw 1
    [Arguments]    ${arg1}=${False}    ${arg2}=${True}
    [Tags]    some_tag    other_tag
    [Documentation]    Some documentation
    ${other_return_value1}    ${some_return_value1} =    Set Variable     123
    ${other_return_value2} =    Set Variable     ${EMPTY}
    Log    ${arg1}
    [Return]    ${False}

My Kw 2
    [Arguments]    ${arg2}=${False}    ${arg4}
    [Tags]    tag1
    [Documentation]    Some documentation.
    ...    In multi line
    Log    ${arg2}
    [Return]    ${arg2}