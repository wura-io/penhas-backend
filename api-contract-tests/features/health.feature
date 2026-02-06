@perl @health
Feature: API Health Check
  Simple health check to verify API is accessible

  Scenario: GET root endpoint returns response
    Given I am testing the "perl" backend
    When I send a GET request to "/"
    Then the response status should be 200 or 404


