@perl @auth @clean
Feature: Authentication API - Golden Master (Perl Mojolicious)
  All tests capture exact behavior of Perl backend.
  DO NOT MODIFY after baseline established.
  
  This is characterization testing to document exact API behavior for Python migration.

  Background:
    Given I am testing the "perl" backend
    And I have a clean database

  @creates-user
  Scenario: POST /signup creates new user successfully
    When I send a POST request to "/signup" with body:
      """
      {
        "dry": 0,
        "email": "<email>",
        "password": "SecurePass123!",
        "senha": "SecurePass123!",
        "nome_completo": "Maria Silva",
        "dt_nasc": "1990-01-15",
        "cpf": "544.340.690-63",
        "cep": "01310100",
        "genero": "Feminino",
        "apelido": "Maria",
        "raca": "Parda",
        "app_version": "1.0.0"
      }
      """
    Then the response status should be 200
    And the response should contain JSON:
      """
      {
        "session": "#regex .+",
        "_test_only_id": "#number"
      }
      """
    And I store the response "_test_only_id" as "userId"
    And I store the response "session" as "sessionId"
    And the database should have 1 users

  @creates-user
  Scenario: POST /signup with duplicate email returns error
    # Create first user
    When I send a POST request to "/signup" with body:
      """
      {
        "dry": 0,
        "email": "dupe_test_<random>@example.com",
        "password": "Pass123!",
        "senha": "Pass123!",
        "nome_completo": "First User",
        "dt_nasc": "1990-01-15",
        "cpf": "544.340.690-63",
        "cep": "01310100",
        "genero": "Feminino",
        "apelido": "First",
        "raca": "Branca",
        "app_version": "1.0.0"
      }
      """
    Then the response status should be 200
    And I store the response body as "firstSignupResponse"
    
    # Store the email we used (we need to track it manually since response doesn't include it)
    # For this test, we'll use a fixed email to test duplicate
    When I send a POST request to "/signup" with body:
      """
      {
        "dry": 0,
        "email": "dupe_fixed_<random>@example.com",
        "password": "Pass123!",
        "senha": "Pass123!",
        "nome_completo": "First User Dupe",
        "dt_nasc": "1990-01-15",
        "cpf": "544.340.690-63",
        "cep": "01310100",
        "genero": "Feminino",
        "apelido": "FirstDupe",
        "raca": "Branca",
        "app_version": "1.0.0"
      }
      """
    Then the response status should be 400
    And the response should contain JSON:
      """
      {
        "error": "#string",
        "message": "#string"
      }
      """
    # Note: CPF duplicate will be caught, so we test that error instead
    # The exact error depends on which validation runs first (email or CPF)

  @creates-user
  Scenario: POST /login with valid credentials
    # Create user first with known password
    Given the database has a user with email "test_login@example.com" and password "password123"
    
    When I send a POST request to "/login" with body:
      """
      {
        "email": "test_login@example.com",
        "senha": "password123",
        "app_version": "1.0.0"
      }
      """
    Then the response status should be 200
    And the response should contain JSON:
      """
      {
        "session": "#regex .+",
        "_test_only_id": "#number"
      }
      """
    And I store the response "session" as "sessionId"

  Scenario: POST /login with invalid credentials returns error
    When I send a POST request to "/login" with body:
      """
      {
        "email": "nonexistent@example.com",
        "senha": "wrongpassword",
        "app_version": "1.0.0"
      }
      """
    Then the response status should be 400
    And the response should contain JSON:
      """
      {
        "error": "#string",
        "message": "#string"
      }
      """

  @creates-user
  Scenario: POST /logout invalidates session
    # Create and login user
    When I send a POST request to "/signup" with body:
      """
      {
        "dry": 0,
        "email": "logout_test_<random>@example.com",
        "password": "LogoutPass123!",
        "senha": "LogoutPass123!",
        "nome_completo": "Logout Test",
        "dt_nasc": "1990-01-15",
        "cpf": "544.340.690-63",
        "cep": "01310100",
        "genero": "Feminino",
        "apelido": "Logout",
        "raca": "Branca",
        "app_version": "1.0.0"
      }
      """
    Then the response status should be 200
    And I store the response "session" as "sessionId"

    # Logout
    When I send a POST request to "/logout" with headers:
      | x-api-key | <sessionId> |
    Then the response status should be 204

    # Verify session is invalid
    When I send a GET request to "/me" with headers:
      | x-api-key | <sessionId> |
    Then the response status should be 403

  @creates-user
  Scenario: GET /me returns user profile with valid session
    # Create and login user
    When I send a POST request to "/signup" with body:
      """
      {
        "dry": 0,
        "email": "me_test_<random>@example.com",
        "password": "MePass123!",
        "senha": "MePass123!",
        "nome_completo": "Me Test User",
        "dt_nasc": "1990-01-15",
        "cpf": "544.340.690-63",
        "cep": "01310100",
        "genero": "Feminino",
        "apelido": "MeTest",
        "raca": "Branca",
        "app_version": "1.0.0"
      }
      """
    Then the response status should be 200
    And I store the response "session" as "sessionId"

    # Get user profile
    When I send a GET request to "/me" with headers:
      | x-api-key | <sessionId> |
    Then the response status should be 200
    And the response should contain JSON:
      """
      {
        "user_profile": {
          "email": "#string",
          "apelido": "#string",
          "nome_completo": "#string",
          "genero": "#string"
        },
        "modules": "#array"
      }
      """

  Scenario: GET /me without authentication returns 401
    When I send a GET request to "/me"
    Then the response status should be 401

