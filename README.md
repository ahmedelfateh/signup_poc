# Dynamic Signup Form System

A flexible, white-label friendly system for creating and managing dynamic form-based user journeys.

## Overview

This Django-based application allows for the creation of customizable form flows that can guide users through different signup journeys. The system supports multiple tenant configurations (white labels), dynamic form schemas, multi-step flows, and detailed tracking of user progress.

## Key Features

- **White-Labeled Forms**: Support multiple brands/tenants with their own custom forms
- **Dynamic Form Schemas**: Create forms using JSON Schema without code changes
- **Multi-Step User Journeys**: Define sequences of forms for different user types
- **User Progress Tracking**: Monitor user completion through signup flows
- **Upgrade Paths**: Support user transitions between journey types (e.g., Demo → Live)
- **Response Scoring**: Calculate and track scores for form responses
- **RESTful API**: Full API access to all system components

## System Architecture

### Core Models

- **WhiteLabel**: Represents different tenants/brands using the system
- **FormSchema**: JSON schema definitions for dynamic forms with optional UI customization
- **FormFlow**: Manages sequences of forms for specific journey types
- **FlowStep**: Connects forms to flows and establishes the step order
- **UserJourney**: Tracks a user's progress through a specific journey flow
- **FormResponse**: Stores user responses to dynamic forms

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/white-labels/` | Manage white label configurations |
| `/schemas/` | Create and manage form schemas |
| `/flows/` | Define form sequences and user journeys |
| `/steps/` | Configure steps within form flows |
| `/journeys/` | Track user progress through journeys |
| `/responses/` | Record and retrieve form submissions |

## Journey Types

The system supports multiple pre-defined journey types:

- **LEAD**: For collecting information from potential users
- **DEMO_USER**: For users in a trial or demo stage
- **LIVE_USER**: For fully onboarded customers

Users can progress from one journey type to another through configured upgrade paths.

## Form Schema System

Forms are defined using JSON Schema, providing flexibility to create any type of form without code changes:

```json
{
  "type": "object",
  "required": ["firstName", "lastName", "email"],
  "properties": {
    "firstName": {"type": "string", "title": "First Name"},
    "lastName": {"type": "string", "title": "Last Name"},
    "email": {"type": "string", "format": "email", "title": "Email"},
    "phoneNumber": {"type": "string", "title": "Phone Number"}
  }
}
```

Additional UI customization is supported through a separate `ui_schema` field.

### Technology References

The FormSchema implementation is based on established standards and libraries:
- [JSON Schema](https://json-schema.org/) - The core schema specification
- [React JSON Schema Form](https://rjsf-team.github.io/react-jsonschema-form/) - Framework for rendering forms from JSON Schema
- [JSONForms](https://jsonforms.io/) - Alternative rendering engine for JSON Schema forms

## Scoring System

The system supports automatic scoring of form responses based on defined score values in the form schema.

### Score Configuration

Add scoring to form fields by including a `score` array with objects defining scores for possible values:

```json
{
  "type": "object",
  "properties": {
    "nationality": {
      "type": "string",
      "enum": ["DE", "IT", "JP", "US", "RU", "Other"],
      "score": [
        {"DE": 1},
        {"IT": 0},
        {"JP": 2},
        {"US": 3},
        {"RU": 1},
        {"Other": 0}
      ],
      "score_type": "normal"
    },
    "experience": {
      "type": "string",
      "enum": ["beginner", "intermediate", "expert"],
      "score": [
        {"beginner": 1},
        {"intermediate": 2},
        {"expert": 3}
      ]
    }
  }
}
```

### Score Calculation Types

The system supports multiple scoring calculation methods:

- **Normal Scoring**: Simple exact match scoring (default)
- **Weighted Scoring**: Apply weights to scores for more complex calculations

Specify the score type using the `score_type` property in the field definition.

### Score Examples

1. **Simple Field Scoring**:
   ```json
   {
     "country": {
       "type": "string",
       "enum": ["US", "UK", "DE"],
       "score": [{"US": 10}, {"UK": 5}, {"DE": 2}]
     }
   }
   ```
   A user selecting "US" would receive 10 points.

2. **Multiple Field Scoring**:
   ```json
   {
     "age": {
       "type": "integer",
       "enum": [18, 25, 35],
       "score": [{"18": 1}, {"25": 2}, {"35": 3}]
     },
     "education": {
       "type": "string",
       "enum": ["high_school", "college", "graduate"],
       "score": [{"high_school": 1}, {"college": 3}, {"graduate": 5}]
     }
   }
   ```
   A user with age 25 and education "graduate" would receive 7 points (2+5).

3. **Nested Object Scoring**:
   ```json
   {
     "preferences": {
       "type": "object",
       "properties": {
         "color": {
           "type": "string",
           "enum": ["red", "blue", "green"],
           "score": [{"red": 3}, {"blue": 5}, {"green": 2}]
         }
       }
     }
   }
   ```
   A user selecting blue as color preference would receive 5 points.

Scores are automatically calculated when form responses are submitted and stored in the `total_score` field of the FormResponse model.

## Setup and Installation

1. Clone the repository
2. Create some virtual env.
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```
   make migrate
   ```
6. Run the development server:
   ```
   make run
   ```

## Usage Examples

### Creating a Form Schema

```python
POST /schemas/
{
  "title": "Contact Information",
  "description": "Basic contact information form",
  "white_label": 1,
  "schema": {
    "type": "object",
    "required": ["firstName", "lastName", "email"],
    "properties": {
      "firstName": {"type": "string", "title": "First Name"},
      "lastName": {"type": "string", "title": "Last Name"},
      "email": {"type": "string", "format": "email", "title": "Email"}
    }
  },
  "is_active": true
}
```

### Creating a User Journey

```python
POST /journeys/
{
  "flow": 1,
  "journey_type": "DEMO_USER",
  "current_step": 1,
  "is_complete": false
}
```

### Submitting a Form Response

```python
POST /responses/
{
  "form_schema": 1,
  "response_data": {
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com"
  },
  "user_journey": 1,
  "flow_step": 1,
  "is_complete": true
}
```

### Creating a Form with Scoring

```python
POST /schemas/
{
  "title": "Risk Assessment Form",
  "description": "Form to assess applicant risk level",
  "white_label": 1,
  "schema": {
    "type": "object",
    "properties": {
      "income": {
        "type": "string",
        "enum": ["0-30k", "30k-60k", "60k-100k", "100k+"],
        "score": [
          {"0-30k": 1},
          {"30k-60k": 2},
          {"60k-100k": 3},
          {"100k+": 4}
        ]
      },
      "creditHistory": {
        "type": "string",
        "enum": ["poor", "fair", "good", "excellent"],
        "score": [
          {"poor": 1},
          {"fair": 2},
          {"good": 3},
          {"excellent": 4}
        ]
      }
    }
  },
  "is_active": true
}
```

## Testing

Run the test suite using pytest:

```
make test
```

The system includes comprehensive tests for all API endpoints and functionality.

## Admin Interface

Access the Django admin interface at `/admin/` to manage all aspects of the system.
