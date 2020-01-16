Feature: Basic search

  Scenario: Run a simple search from main page
    Given Main page is loaded
    When we type search phrase into search box and click Enter
    Then we receive correct search results