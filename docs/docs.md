
# Rpg-system

This is a project that targets to intoduce the reward system in games into peoples schedules. I takes the concepts of gamifying tasks and making them feel less of a chore but a fun and enjoyable quest.

<!--- If we have only one group/collection, then no need for the "ungrouped" heading -->



## Endpoints

* [Activites](#activites)
    1. [Fetch activities](#1-fetch-activities)
        * [Fetch activities-no activity id specified](#i-example-request-fetch-activities-no-activity-id-specified)
        * [filtering activity id](#ii-example-request-filtering-activity-id)
    1. [Create an activity](#2-create-an-activity)
        * [Create an activity](#i-example-request-create-an-activity)
    1. [Modify activity](#3-modify-activity)
        * [Modify activity](#i-example-request-modify-activity)
* [sub-activities](#sub-activities)
    1. [Create a sub activity](#1-create-a-sub-activity)
        * [Create a sub activity](#i-example-request-create-a-sub-activity)
    1. [sub acitivty modificaiton](#2-sub-acitivty-modificaiton)
        * [sub acitivty modificaiton](#i-example-request-sub-acitivty-modificaiton)
    1. [delete subactivity](#3-delete-subactivity)
* [complete-activites](#complete-activites)
    1. [complete task](#1-complete-task)
        * [complete task-skipped](#i-example-request-complete-task-skipped)
        * [complete task-completed](#ii-example-request-complete-task-completed)
        * [complete task-partial](#iii-example-request-complete-task-partial)
        * [complete task- buffer activites](#iv-example-request-complete-task--buffer-activites)
    1. [finalize the days events](#2-finalize-the-days-events)
        * [finalize the days events](#i-example-request-finalize-the-days-events)
* [schedule-tasks](#schedule-tasks)
    1. [create timetable](#1-create-timetable)
        * [create timetable](#i-example-request-create-timetable)
    1. [schudule-task](#2-schudule-task)
        * [schudule-task](#i-example-request-schudule-task)
    1. [retireve tasks scheduled](#3-retireve-tasks-scheduled)
        * [retireve tasks scheduled](#i-example-request-retireve-tasks-scheduled)
    1. [retrieve information about a task](#4-retrieve-information-about-a-task)
        * [retrieve information about a task](#i-example-request-retrieve-information-about-a-task)
    1. [modify activity](#5-modify-activity)
        * [modify activity](#i-example-request-modify-activity-1)
    1. [delete a scheduled task](#6-delete-a-scheduled-task)
    1. [get activites stats](#7-get-activites-stats)
        * [get activites stats](#i-example-request-get-activites-stats)
    1. [get tasks to schedule](#8-get-tasks-to-schedule)
        * [get tasks to schedule](#i-example-request-get-tasks-to-schedule)
* [stats](#stats)
    1. [get user's stats](#1-get-users-stats)
        * [get user's stats](#i-example-request-get-users-stats)

--------



## Activites



### 1. Fetch activities


### GET /api/activities

Make a GET request to fetch activities for a certain user. Provide the `id` as a query parameter to filter out activities that match the specified id.

#### Query Parameters

- `id` (integer, required): The activity ID to filter activities.
    

The server responds with a list of JSON objects representing the sub-activities associated with the specified activity ID.

#### Response

The response will be an array of `activities` objects, each containing the following fields:

- `created_at` (string): The timestamp of when the activity was created.
    
- `id` (integer): The ID of the activity.
    
- `name` (string): The name of the activity.
    
- `sub_activities` (array): An array of sub-activities, each containing the following fields:
    
    - `activity_id` (integer): The ID of the parent activity.
        
    - `attribute_weights` (object): An object containing attribute weights for the sub-activity.
        
    - `base_exp` (integer): The base experience points for the sub-activity.
        
    - `difficulty_multiplier` (float): The difficulty multiplier for the sub-activity.
        
    - `id` (integer): The ID of the sub-activity.
        
    - `name` (string): The name of the sub-activity.
        
    - `scheduled_time` (integer): The scheduled time for the sub-activity.


***Endpoint:***

```bash
Method: GET
Type: 
URL: {{port-500}}/api/activities
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | 49f8185a-c2bb-4167-8eb3-f9d3167f9c5e |  |
| id | 3 |  |



***More example Requests/Responses:***


#### I. Example Request: Fetch activities-no activity id specified



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | 49f8185a-c2bb-4167-8eb3-f9d3167f9c5e |  |



***Body: None***



#### I. Example Response: Fetch activities-no activity id specified
```js
{
    "activities": [
        {
            "created_at": "2025-05-23T11:22:33.654262",
            "id": 3,
            "name": "Daily Workout",
            "sub_activities": [
                {
                    "activity_id": 3,
                    "attribute_weights": {
                        "DSC": 0.2,
                        "FCS": 0.3,
                        "STA": 0.5
                    },
                    "base_exp": 80,
                    "difficulty_multiplier": 1,
                    "id": 3,
                    "name": "Morning Cycling",
                    "scheduled_time": 45
                }
            ]
        },
        {
            "created_at": "2025-05-23T12:00:40.134363",
            "id": 5,
            "name": "Context switch",
            "sub_activities": [
                {
                    "activity_id": 5,
                    "attribute_weights": {},
                    "base_exp": 0,
                    "difficulty_multiplier": 1,
                    "id": 5,
                    "name": "Short Break",
                    "scheduled_time": 15
                }
            ]
        }
    ]
}
```


***Status Code:*** 200

<br>



#### II. Example Request: filtering activity id



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | 49f8185a-c2bb-4167-8eb3-f9d3167f9c5e |  |
| id | 3 |  |



***Body: None***



#### II. Example Response: filtering activity id
```js
{
    "activities": [
        {
            "created_at": "2025-05-23T11:22:33.654262",
            "id": 3,
            "name": "Daily Workout",
            "sub_activities": [
                {
                    "activity_id": 3,
                    "attribute_weights": {
                        "DSC": 0.2,
                        "FCS": 0.3,
                        "STA": 0.5
                    },
                    "base_exp": 80,
                    "difficulty_multiplier": 1,
                    "id": 3,
                    "name": "Morning Cycling",
                    "scheduled_time": 45
                },
                {
                    "activity_id": 3,
                    "attribute_weights": {
                        "CHA": 0,
                        "DSC": 0.3,
                        "FCS": 0.3,
                        "INT": 0,
                        "STA": 0.4
                    },
                    "base_exp": 100,
                    "difficulty_multiplier": 1,
                    "id": 6,
                    "name": "running",
                    "scheduled_time": 60
                }
            ]
        }
    ]
}
```


***Status Code:*** 200

<br>



### 2. Create an activity


On a succesful activity creation

``` json
{
    "created_at": "2025-05-11T22:30:42.576415",
    "id": 11,
    "name": "Test activity 4"
}

 ```

If duplicaion occurs

``` json
{
    "args": [
        "Acivity already exist. Test activity 2"
    ],
    "description": "RecordDuplicationError('Acivity already exist. Test activity 2')",
    "msg": "Acivity already exist. Test activity 2",
    "type": "RecordDuplicationError"
}

 ```


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: {{port-500}}/api/activities
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "name":"Work out"
}
```



***More example Requests/Responses:***


#### I. Example Request: Create an activity



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "name":"Work out"
}
```



#### I. Example Response: Create an activity
```js
{
    "created_at": "2025-05-23T11:22:33.654262",
    "id": 3,
    "name": "Work out"
}
```


***Status Code:*** 201

<br>



### 3. Modify activity


Modify access acitivity ie the name.

Server responsds with a 404 if the activity is not found.

``` json
{ "args": [ "No activity with id <id>" ], "description": "RecordNotFoundError(&#x27;No activity with id <id>&#x27;)", "kwargs": { "message": "No activity with id 88", "status_code": 404 }, "msg": "No activiy mathing the id <id>", "type": ""}

 ```

Responds with

``` json
{
  "created_at": "2025-05-11T20:03:17.171617",
  "id": 8,
  "name": "<Modified activity 1>"
}

 ```


***Endpoint:***

```bash
Method: PUT
Type: RAW
URL: {{port-500}}/api/activity/3
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "name": "Daily Workout"
}
```



***More example Requests/Responses:***


#### I. Example Request: Modify activity



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "name": "Daily Workout"
}
```



#### I. Example Response: Modify activity
```js
{
    "created_at": "2025-05-23T11:22:33.654262",
    "id": 3,
    "name": "Daily Workout"
}
```


***Status Code:*** 200

<br>



## sub-activities



### 1. Create a sub activity


The `POST` request creates a new subactivity and associates it with a parent activity. The request should include the `activity_id`, `name`, `difficulty_multiplier`, `scheduled_time`, `base_exp`, and `attribute_weights` in the JSON body. The `attribute_weights` should contain the weights for attributes such as STA, DSC, and FCS.

### Error Scenarios

1. When the `activity_id` is not included in the JSON body, the server returns an `InvalidRequestData` error with a message indicating the missing key.
    
2. If the `activity_id` does not exist or does not belong to the logged-in user, an `AuthorizationError` is returned with a corresponding message.
    
3. When certain subactivity data is missing or invalid, the server returns an `InvalidRequestData` error with details about the missing or invalid data.
    
4. If a subactivity duplication is detected, the server responds with a `RecordDuplicationError` indicating the duplication.
    

### Example Response

``` json
{
    "activity_id": 0,
    "attribute_weights": {
        "DSC": 0,
        "FCS": 0,
        "STA": 0
    },
    "base_exp": 0,
    "difficulty_multiplier": 0,
    "id": 0,
    "name": "",
    "scheduled_time": ""
}

 ```

There are various responses the server returns depending on the request data sent.

1. **ERRORS**
    
    1. when parent activity id is not included in the json body.
        

``` json
{
    "args": [
        "Key error 'activity_id not in request's json' "
    ],
    "description": "InvalidRequestDAta(\"Key error 'activity_id not in request's json' \")",
    "msg": "Key error 'activity_id not in request's json' ",
    "type": "InvalidRequestDAta"
}

 ```

b. When the activiy id does not exist or it does not belong to the logged in user.

``` json
{
    "args": [
        "Can only modify activites you created "
    ],
    "description": "AuthorizationError('Can only modify activites you created ')",
    "msg": "Can only modify activites you created ",
    "type": "AuthorizationError"
}

 ```

c. If certain subactivity data is missing or invalid

``` json
{
    "args": [
        "Mising activity keys :['attribute_weights']"
    ],
    "description": "InvalidRequestDAta(\"Mising activity keys :['attribute_weights']\")",
    "msg": "Mising activity keys :['attribute_weights']",
    "type": "InvalidRequestDAta"
}
{
    "args": [
        "All attributes weights must add up to 1 {'INT': 10}"
    ],
    "description": "InvalidRequestDAta(\"All attributes weights must add up to 1 {'INT': 10}\")",
    "msg": "All attributes weights must add up to 1 {'INT': 10}",
    "type": "InvalidRequestDAta"
}

 ```

d. Duplication of an activity.

``` json
{
    "args": [
        "Sub activity duplication detected Sub 4"
    ],
    "description": "RecordDuplicationError('Sub activity duplication detected Sub 4')",
    "msg": "Sub activity duplication detected Sub 4",
    "type": "RecordDuplicationError"
}

 ```


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: {{port-500}}/api/subactivity
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "activity_id":3,
    "name":"Cycling",
    "difficulty_multiplier":1,
    "scheduled_time":60,
    "base_exp":120,
    "attribute_weights":{"STA":0.5,"DSC":0.3 ,"FCS":0.2}
   

}
```



***More example Requests/Responses:***


#### I. Example Request: Create a sub activity



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "activity_id":3,
    "name":"Cycling",
    "difficulty_multiplier":1,
    "scheduled_time":60,
    "base_exp":120,
    "attribute_weights":{"STA":0.5,"DSC":0.3 ,"FCS":0.2}
   

}
```



#### I. Example Response: Create a sub activity
```js
{
    "activity_id": 3,
    "attribute_weights": {
        "DSC": 0.3,
        "FCS": 0.2,
        "STA": 0.5
    },
    "base_exp": 120,
    "difficulty_multiplier": 1,
    "id": 3,
    "name": "Cycling",
    "scheduled_time": "60"
}
```


***Status Code:*** 201

<br>



### 2. sub acitivty modificaiton


Modify different values of the sub activity. Serve will respond with a 400 incase the new values do follow the expected format.

All authorizaion applied during creation al also present.

eg Weights exceeding 1.

``` json
{
    "args": [
        "All attributes weights must add up to 1 {'INT': 0.5, 'FCS': 0.8, 'DSC': 0.2}"
    ],
    "description": "InvalidRequestDAta(\"All attributes weights must add up to 1 {'INT': 0.5, 'FCS': 0.8, 'DSC': 0.2}\")",
    "msg": "All attributes weights must add up to 1 {'INT': 0.5, 'FCS': 0.8, 'DSC': 0.2}",
    "type": "InvalidRequestDAta"
}

 ```

To modify the starting time ,the time_zone must also be included in the request body.

``` json
{
    "args": [
        "starts_at must be accompanied by time_zone"
    ],
    "description": "InvalidRequestDAta('starts_at must be accompanied by time_zone')",
    "msg": "starts_at must be accompanied by time_zone",
    "type": "InvalidRequestDAta"
}

 ```


***Endpoint:***

```bash
Method: PUT
Type: RAW
URL: {{port-500}}/api/subactivity/3
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "name":"Morning Cycling",
    "attribute_weights":{"STA":0.5 ,"FCS":0.3,"DSC":0.2},
    "starts_at":"2024-04-02T19:56",
    "scheduled_time":45,
    "base_exp":80
    
}
```



***More example Requests/Responses:***


#### I. Example Request: sub acitivty modificaiton



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "name":"Morning Cycling",
    "attribute_weights":{"STA":0.5 ,"FCS":0.3,"DSC":0.2},
    "starts_at":"2024-04-02T19:56",
    "scheduled_time":45,
    "base_exp":80
    
}
```



#### I. Example Response: sub acitivty modificaiton
```js
{
    "activity_id": 3,
    "attribute_weights": {
        "DSC": 0.2,
        "FCS": 0.3,
        "STA": 0.5
    },
    "base_exp": 80,
    "difficulty_multiplier": 1,
    "id": 3,
    "name": "Morning Cycling"
}
```


***Status Code:*** 200

<br>



### 3. delete subactivity


Deactivate a subactivity but can be activated again in the post method.


***Endpoint:***

```bash
Method: DELETE
Type: 
URL: {{port-500}}/api/subactivity/3
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



## complete-activites

### 1\. Complete Activity

**Endpoint:** `/complete_activity`  
**Method:** POST

This endpoint allows users to mark a timetable entry as completed, partially completed, or skipped.

#### Request Body

- `timetable_entry_id` (int, required): ID of the timetable entry to complete
- `status` (str, required): Completion status ('completed', 'skipped', 'partial')
- `completed_on` (str, required): Date and time of completion (format: "YYYY-MM-DD HH:MM:SS")
- `actual_time_taken` (int, optional): Actual time spent in minutes
- `reason` (str, optional): Reason for skipped/partial completion
- `comment` (str, optional): Additional comments
    

#### Response

Returns a JSON object containing:

- `completion_id`: ID of the created completion log
- `status`: Status of the completion
- `exp_change`: EXP gained or lost
- `attributes`: Updated user attributes (INT, STA, FCS, CHA, DSC)
    

### 2\. Finalize Day

**Endpoint:** `/finalize_day`  
**Method:** POST

This endpoint finalizes the day's events and calculates the overall day's gained EXP.

#### Request Body

- `date` (str, required): Date to finalize (format: "YYYY-MM-DD")
    

#### Response

Returns a JSON object containing:

- `new_total_exp`: Updated total EXP for the user
- `level`: Current user level
- `level_up`: Boolean indicating if a level up occurred
- `attributes`: Updated user attributes (INT, STA, FCS, CHA, DSC)
- `level_up_details` (if applicable): Information about the new level and rewards
    

## Rules and Expected Parameters

1. **Completion Status**
    - Valid statuses: 'completed', 'skipped', 'partial'
    - Each status has specific parameter requirements
2. **Completed Status**
    - Required: `timetable_entry_id`, `status`, `completed_on`
    - Optional: `actual_time_taken`, `comment`
    - `completed_on` must be within the grace period (15 minutes) of the scheduled end time for full EXP
3. **Partial Status**
    - Required: `timetable_entry_id`, `status`, `completed_on`, `actual_time_taken`, `reason`
    - Optional: `comment`
    - `actual_time_taken` must be less than the scheduled time
4. **Skipped Status**
    - Required: `timetable_entry_id`, `status`, `completed_on`, `reason`
    - Optional: `comment`
5. **Time Format**
    - `completed_on` must be in the format "YYYY-MM-DD HH:MM:SS"
    - `date` for finalizing day must be in the format "YYYY-MM-DD"
6. **EXP Calculation**
    - EXP is calculated based on the activity's base EXP, difficulty multiplier, scheduled time, and completion status
    - Late completion results in EXP deductions
    - Skipped activities result in negative EXP
7. **Finalizing the Day**
    - All scheduled tasks for the day must be completed, partially completed, or skipped before finalizing
    - The day's discipline factor (dcp) affects the total EXP gained
8. **Level Up**
    - Level up occurs when the user's total EXP reaches or exceeds the next level's required EXP
    - Level up may unlock new rewards or privileges



### 1. complete task


### Complete Activity

---

This API endpoint is used to complete an activity.

#### Request

- Method: `POST`
    
- URL: `{{port-500}}/api/complete/complete_activity?tkn={{testing-rpg-tkn}}`
    
- Headers:
    
    - Content-Type: `application/json`
        
- { "timetable_entry_id": 5, "status": "partial", "completed_on": "2024-09-10T07:05", "actual_time_taken": 60, "reason": "The task was more difficult th ...", "comment": "I found in extremely exhaustin ..." }
    

#### Response

- Status: 201
    
- Content-Type: application/json
    
- { "attributes": { "CHA": 0, "DSC": 0, "FCS": 0, "INT": 0, "STA": 0 }, "completion_id": 0, "exp_change": null, "status": "" }
    
- { "attributes": { "CHA": 0, "DSC": 0, "FCS": 0, "INT": 0, "STA": 0 }, "completion_id": 0, "exp_change": 0, "status": "" }
    

#### Error Messages

- InvalidRequestData('completed_on needs to be informat %Y-%m-%dT%H:%M') should be corrected to InvalidRequestData('completed_on needs to be in the format %Y-%m-%dT%H:%M')
    
- RecordDuplicationError('Task already logged for this day') should be corrected to RecordDuplicationError('Task already logged for this day.')
    

#### Expected Response

``` json
{
    "attributes": {
        "CHA": 218,
        "DSC": 178,
        "FCS": 101,
        "INT": 202,
        "STA": 0
    },
    "completion_id": 7,
    "exp_change": 195,
    "status": "completed"
}

 ```

``` json
{
    "description": "InvalidRequestData(\"Missing required fields: ['timetable_entry_id', 'status', 'completed_on']\")",
    "msg": "Missing required fields: ['timetable_entry_id', 'status', 'completed_on']",
    "type": "InvalidRequestData"
}

 ```

``` json
{
    "description": "InvalidRequestData('completed_on needs to be informat %Y-%m-%dT%H:%M')",
    "msg": "completed_on needs to be informat %Y-%m-%dT%H:%M",
    "type": "InvalidRequestData"
}

 ```

``` json
{
    "description": "InvalidRequestData('Completion time does not match the date of the timetable entry')",
    "msg": "Completion time does not match the date of the timetable entry",
    "type": "InvalidRequestData"
}

 ```

``` json
{
    "description": "RecordDuplicationError('Task already logged for this day')",
    "msg": "Task already logged for this day",
    "type": "RecordDuplicationError"
}

 ```

- Expected response is
    

``` json
{
    "attributes": {
        "CHA": 218,
        "DSC": 178,
        "FCS": 101,
        "INT": 202,
        "STA": 0
    },
    "completion_id": 7,
    "exp_change": 195,
    "status": "completed"
}

 ```

- For tasks with status `completed` , the reason can be ommited if the task was completed within the grace period.
    
- For skipped tasks, the value `completed_on` can be ignored.
    
- Buffer activites will have their `exp_change` as null and not 0.


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: {{port-500}}/api/complete/complete_activity
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "timetable_entry_id": 5,
    "status": "completed",
    "completed_on": "2024-09-10T07:05",
    "actual_time_taken": 60,
    "reason": "The task was more difficult than I expected, but I am glad I pushed through.",
    "comment": "I found it extremely exhausting but helpful."
}

```



***More example Requests/Responses:***


#### I. Example Request: complete task-skipped



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "timetable_entry_id": 5,
    "status": "skipped",
    "reason":"I slept in. ",
    "comment":"I should'n have skipped this task. "
}
```



#### I. Example Response: complete task-skipped
```js
{
    "attributes": {
        "CHA": 0,
        "DSC": -12,
        "FCS": -19,
        "INT": 0,
        "STA": -32
    },
    "completion_id": 4,
    "exp_change": -64,
    "status": "skipped"
}
```


***Status Code:*** 201

<br>



#### II. Example Request: complete task-completed



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "timetable_entry_id": 6,
    "status": "completed",
    "completed_on": "2024-09-10T07:05",//Can be excluded from the json body is status is skipped. 
    "actual_time_taken":60,
    "reason":"The task was more difficult than i expected but am glad i pushed on.", // This is only a requirement if the completion is not within the grace period.
    "comment":"I should have skipped this task. "
}
```



#### II. Example Response: complete task-completed
```js
{
    "attributes": {
        "CHA": 0,
        "DSC": 3,
        "FCS": 3,
        "INT": 0,
        "STA": 7
    },
    "completion_id": 4,
    "exp_change": 66,
    "status": "completed"
}
```


***Status Code:*** 201

<br>



#### III. Example Request: complete task-partial



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "timetable_entry_id": 5,
    "status": "partial",
    "completed_on": "2024-09-10T07:05",//Can be excluded from the json body is status is skipped. 
    "actual_time_taken":60,
    "reason":"The task was more difficult than i expected but am glad i pushed on.",
    "comment":"I found in extremely exhausting but helpfull. "
}
```



#### III. Example Response: complete task-partial
```js
{
    "attributes": {
        "CHA": 0,
        "DSC": 12,
        "FCS": 16,
        "INT": 0,
        "STA": 30
    },
    "completion_id": 4,
    "exp_change": 46,
    "status": "partial"
}
```


***Status Code:*** 201

<br>



#### IV. Example Request: complete task- buffer activites



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "timetable_entry_id": 6,
    "status": "partial",
    "completed_on": "2024-09-10T07:05",//Can be excluded from the json body is status is skipped. 
    "actual_time_taken":60,
    "reason":"The task was more difficult than i expected but am glad i pushed on.",
    "comment":"I found in extremely exhausting but helpfull. "
}
```



#### IV. Example Response: complete task- buffer activites
```js
{
    "attributes": {
        "CHA": 0,
        "DSC": 12,
        "FCS": 16,
        "INT": 0,
        "STA": 30
    },
    "completion_id": 5,
    "exp_change": null,
    "status": "partial"
}
```


***Status Code:*** 201

<br>



### 2. finalize the days events


- The date the request is supposed to triger summarization for should be in the body or else server will respond with a 400
    

``` json
{
    "description": "InvalidRequestData('date is a required filed in the json body. ')",
    "msg": "date is a required in the json body. ",
    "type": "InvalidRequestData"
}

 ```

- If there are pending task in the days schedule, server will respond with a.
    

``` json
{
    "incompletetasks": {
        "description": "IncompleteTasks('Cannot finalize day. Incomplete tasks still exist.')",
        "msg": "Cannot finalize day. Incomplete tasks still exist.",
        "type": "IncompleteTasks"
    },
    "names": [
        "Mathematics",
        "Computer Science"
    ]
}

 ```

- A day can only be finalized once.
    

``` json
{
    "description": "RecordDuplicationError('Timetable for the given date is already finalized.')",
    "msg": "Timetable for the given date is already finalized.",
    "type": "RecordDuplicationError"
}

 ```

- If no error occured the response is similar to .
    

``` json
{
    "attributes": {
        "CHA": 299,
        "DSC": 233,
        "FCS": 101,
        "INT": 202,
        "STA": 0
    },
    "level": 1,
    "level_up": false,
    "new_total_exp": 1012
}

 ```


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: {{port-500}}/api/complete/finalize_day
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        

{
    "date":"2024-09-10"
}
```



***More example Requests/Responses:***


#### I. Example Request: finalize the days events



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        

{
    "date":"2024-09-10"
}
```



#### I. Example Response: finalize the days events
```js
{
    "attributes": {
        "CHA": 0,
        "DSC": 12,
        "FCS": 16,
        "INT": 0,
        "STA": 30
    },
    "level": 1,
    "level_up": false,
    "new_total_exp": 46
}
```


***Status Code:*** 200

<br>



## schedule-tasks

This folder contains endpoints that are used to schedule tasks.



### 1. create timetable


Create a timetable record for a certain data

return 400 if date is missing or is in the wrong forma

``` json
{
    "args": [
        "Date is required"
    ],
    "description": "InvalidRequestData('Date is required')",
    "msg": "Date is required",
    "type": "InvalidRequestData"
}

 ```

if the request was successfule. Server responds with 201 and

``` json
{
    "date": "2024-09-09",
    "goal_text": null,
    "id": 8
}

 ```

Trying to create a timtable with the same date will result in the error below.

``` json
{
    "args": [
        "Time table duplication detected."
    ],
    "description": "RecordDuplicationError('Time table duplication detected.')",
    "msg": "Time table duplication detected.",
    "type": "RecordDuplicationError"
}

 ```


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: {{port-500}}/api/timetable/create
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "date":"2024-09-10",
    "goal_text":"Test date creation"
}
```



***More example Requests/Responses:***


#### I. Example Request: create timetable



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "date":"2024-09-10",
    "goal_text":"Test date creation"
}
```



#### I. Example Response: create timetable
```js
{
    "date": "2024-09-10",
    "goal_text": "Test date creation",
    "id": 4
}
```


***Status Code:*** 201

<br>



### 2. schudule-task


Schedule a task within a timetable.

The request needs to meet the requirements and include all mandatory fileds otherwise the serve returns.

``` json
{
    "description": "InvalidRequestData(\"Missing required fields ['sub_activity_id', 'date', 'start_time', 'end_time']\")",
    "msg": "Missing required fields ['sub_activity_id', 'date', 'start_time', 'end_time']",
    "type": "InvalidRequestData"
}

 ```

The time formatin must match the documented format or else an error response.

``` json
{
    "description": "InvalidRequestData(\"time data '09-09' does not match format '%H:%M'\")",
    "msg": "time data '09-09' does not match format '%H:%M'",
    "type": "InvalidRequestData"
}

 ```

On successefule scheduling , the server reponds with a 201. if the param create_buffer was set to faks, buffer_task is returned as null.

``` json
{
    "buffer_task": {
        "end_time": "07:48:00",
        "id": 70,
        "start_time": "07:33:00",
        "timetable_id": 8
    },
    "main_task": {
        "end_time": "07:33:00",
        "id": 69,
        "start_time": "06:33:00",
        "timetable_id": 8
    }
}

 ```


***Endpoint:***

```bash
Method: POST
Type: RAW
URL: {{port-500}}/api/timetable/task
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "sub_activity_id":3,
    "date":"2024-09-10",
    "start_time":"06:00",
    "time_zone":"Africa/Nairobi",
    //The parameter below are optional
    "task_duration":null,//how long the task will run. server defaults to subactivity.schedule_time.
    "create_buffer":true,//whether the system to append a buffer activity. server default is true
    "cyclic":true,//whether the task iscylic or not. server default is false
    "buffer_name":"Testing buffer",//The buffer actifiby to hold subactivities used to facilitate context switch. server default is 'Context Switch'
    "specifi_buffer_name":"Short break" //sub activity name used to separate scheduled tasks. server defaults to 'Short Break'
}
```



***More example Requests/Responses:***


#### I. Example Request: schudule-task



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
{
    "sub_activity_id":3,
    "date":"2024-09-10",
    "start_time":"06:00",
    "time_zone":"Africa/Nairobi",
    //The parameter below are optional
    "task_duration":null,//how long the task will run. server defaults to subactivity.schedule_time.
    "create_buffer":true,//whether the system to append a buffer activity. server default is true
    "cyclic":true,//whether the task iscylic or not. server default is false
    "buffer_name":"Testing buffer",//The buffer actifiby to hold subactivities used to facilitate context switch. server default is 'Context Switch'
    "specifi_buffer_name":"Short break" //sub activity name used to separate scheduled tasks. server defaults to 'Short Break'
}
```



#### I. Example Response: schudule-task
```js
{
    "buffer_task": {
        "activity_name": "Short Break",
        "cyclic": false,
        "end_time": "07:00:00",
        "id": 6,
        "start_time": "06:45:00",
        "timetable_id": 4,
        "weekday": null
    },
    "main_task": {
        "activity_name": "Morning Cycling",
        "cyclic": true,
        "end_time": "06:45:00",
        "id": 5,
        "start_time": "06:00:00",
        "timetable_id": 4,
        "weekday": 2
    }
}
```


***Status Code:*** 201

<br>



### 3. retireve tasks scheduled


Rertieve entries scheduled for a certain date.

Date must match the format YYYYY-MM-DD if not the response is.

A days argument can be passed in the url to retrieve schedules within range of the date passed and the amount of days set.

``` json
{
    "description": "InvalidRequestData('Invalid date format. Use YYYY-MM-DD')",
    "msg": "Invalid date format. Use YYYY-MM-DD",
    "type": "InvalidRequestData"
}

 ```

``` json
{
    "schedule": {
        "2024-09-09": [
            {
                "end_time": "07:33:00",
                "id": 69,
                "start_time": "06:33:00",
                "timetable_id": 8
            },
            {
                "end_time": "07:48:00",
                "id": 70,
                "start_time": "07:33:00",
                "timetable_id": 8
            },
            {
                "end_time": "10:00:00",
                "id": 21,
                "start_time": "09:00:00",
                "timetable_id": 3
            },
            {
                "end_time": "13:15:00",
                "id": 25,
                "start_time": "12:15:00",
                "timetable_id": 3
            },
            {
                "end_time": "15:45:00",
                "id": 29,
                "start_time": "15:15:00",
                "timetable_id": 3
            }
        ],
        "2024-09-10": []
    },
    "start_date": "2024-09-09"
}

 ```


***Endpoint:***

```bash
Method: GET
Type: 
URL: {{port-500}}/api/timetable/info/2024-09-10
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |
| days | 1 |  |



***More example Requests/Responses:***


#### I. Example Request: retireve tasks scheduled



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |
| days | 1 |  |



***Body: None***



#### I. Example Response: retireve tasks scheduled
```js
{
    "schedule": {
        "2024-09-10": [
            {
                "activity_name": "Morning Cycling",
                "cyclic": true,
                "end_time": "06:45:00",
                "id": 5,
                "start_time": "06:00:00",
                "timetable_id": 4,
                "weekday": 2
            },
            {
                "activity_name": "Short Break",
                "cyclic": false,
                "end_time": "07:00:00",
                "id": 6,
                "start_time": "06:45:00",
                "timetable_id": 4,
                "weekday": null
            }
        ]
    },
    "start_date": "2024-09-10"
}
```


***Status Code:*** 200

<br>



### 4. retrieve information about a task


Get information about a specific scheduled task.

``` json
{
    "activity_name": "testing apis",
    "end_time": "07:33:00",
    "id": 69,
    "start_time": "06:33:00",
    "timetable_id": 8
}

 ```


***Endpoint:***

```bash
Method: GET
Type: 
URL: {{port-500}}/api/timetable/task/5
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***More example Requests/Responses:***


#### I. Example Request: retrieve information about a task



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body: None***



#### I. Example Response: retrieve information about a task
```js
{
    "activity_name": "Morning Cycling",
    "cyclic": null,
    "end_time": "06:45:00",
    "id": 5,
    "start_time": "06:00:00",
    "timetable_id": 4,
    "weekday": null
}
```


***Status Code:*** 200

<br>



### 5. modify activity


Modify specific entries.

items that can be modifed are:

- start time
- end time
- cyclic
- weekday
- subactivity id
    

server may respond with 207 if cyclic was modified but the weekday number was not set.

- case 1.
    - modifying the cyclic attribute without passing the weekday number. as sample response is shown below.

``` json
response:
{
  "activity_name": "testing apis",
  "customwarnings": {
    "description": "CustomWarnings('Week day was not provided. Defaulting to week day from 2024-09-09')",
    "msg": "Week day was not provided. Defaulting to week day from 2024-09-09",
    "type": "CustomWarnings"
  },
  "cyclic": true,
  "end_time": "05:33:00",
  "id": 69,
  "start_time": "03:33:00",
  "timetable_id": 8,
  "weekday": 1
}

 ```

- Case 2.
    - csetting the subactivity will alter the scheduled task with the set target id
    - sample of the request body is.

``` json
 {
    "cyclic":true,
    "start_time":"06:00",
    "end_time":"08:00",
    "time_zone":"Africa/Nairobi",
    "sub_activity_id": 4 //Only for swaping target schedules with others sub activities..
}

 ```

the response is

``` json
{
  "activity_name": "Computer Science",
  "customwarnings": {
    "description": "CustomWarnings('Week day was not provided. Defaulting to week day from 2024-09-09')",
    "msg": "Week day was not provided. Defaulting to week day from 2024-09-09",
    "type": "CustomWarnings"
  },
  "cyclic": true,
  "end_time": "05:33:00",
  "id": 69,
  "start_time": "03:33:00",
  "timetable_id": 8,
  "weekday": 1
}

 ```

- Case 3.
    
    - setting the weekday manually removes the warnig .
        
- Request body and the response.
    

``` json
 {
    "cyclic":true,
    "start_time":"06:00",
    "end_time":"08:00",
    "time_zone":"Africa/Nairobi",
    "sub_activity_id": 4, //Only for swaping target schedules with others sub activities. 
    "weekday":1// Usefulll when one wants to alter the cyclic pattern for a certain task.

}


 ```

``` json
{
  "activity_name": "Computer Science",
  "cyclic": true,
  "end_time": "05:33:00",
  "id": 69,
  "start_time": "03:33:00",
  "timetable_id": 8,
  "weekday": 1
}

 ```


***Endpoint:***

```bash
Method: PUT
Type: RAW
URL: {{port-500}}/api/timetable/task/5
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
 {
    "cyclic":true,
    "start_time":"06:00",
    "end_time":"06:50",
    "time_zone":"Africa/Nairobi",
    // "sub_activity_id": 4, // Only for swapping target schedules with other sub activities. 
    "weekday": 1 // Useful when one wants to alter the cyclic pattern for a certain task.
}

```



***More example Requests/Responses:***


#### I. Example Request: modify activity



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body:***

```js        
 {
    "cyclic":true,
    "start_time":"06:00",
    "end_time":"06:50",
    "time_zone":"Africa/Nairobi",
    // "sub_activity_id": 4, // Only for swapping target schedules with other sub activities. 
    "weekday": 1 // Useful when one wants to alter the cyclic pattern for a certain task.
}

```



#### I. Example Response: modify activity
```js
{
    "activity_name": "Morning Cycling",
    "cyclic": true,
    "end_time": "06:50:00",
    "id": 5,
    "start_time": "06:00:00",
    "timetable_id": 4,
    "weekday": 1
}
```


***Status Code:*** 200

<br>



### 6. delete a scheduled task


Delete a schedules task . if the request was succusseful the response code is 204. e

responsds with 404 if record does not exixt.

``` json
{
  "description": "RecordNotFoundError('Record not found.')",
  "msg": "Record not found.",
  "type": "RecordNotFoundError"
}


 ```


***Endpoint:***

```bash
Method: DELETE
Type: 
URL: {{port-500}}/api/timetable/task/69
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



### 7. get activites stats


Get stats about certain activites that are within the date range specified by hte arguments.

- days
    - how many days to span
- date
    - The starting date.
    - Expected format is
        - YYYY-MM-DD
- Passing the wrong date or time will result in errors.
    

``` json
{
  "description": "InvalidRequestData('Invalid date format %Y-%m-%d')",
  "msg": "Invalid date format %Y-%m-%d",
  "type": "InvalidRequestData"
}

 ```

- days must be integers.
    

``` json
{
  "description": "InvalidRequestData(ValueError('Days must be greater than 1'))",
  "msg": "Days must be greater than 1",
  "type": "InvalidRequestData"
}
{
  "description": "InvalidRequestData(ValueError(\"invalid literal for int() with base 10: 'i'\"))",
  "msg": "invalid literal for int() with base 10: 'i'",
  "type": "InvalidRequestData"
}


 ```


***Endpoint:***

```bash
Method: GET
Type: 
URL: {{port-500}}/api/timetable/stats
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |
| date | 2024-09-10 |  |
| days | 1 |  |



***More example Requests/Responses:***


#### I. Example Request: get activites stats



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |
| date | 2024-09-10 |  |
| days | 1 |  |



***Body: None***



#### I. Example Response: get activites stats
```js
{
    "activities": {
        "Context switch": {
            "count": 1,
            "hours": 0.16666666666666666
        },
        "Daily Workout": {
            "count": 1,
            "hours": 0.8333333333333334
        }
    },
    "total_hours": 1,
    "total_tasks": 2
}
```


***Status Code:*** 200

<br>



### 8. get tasks to schedule


- Get a a json object representing tasks and activites one can schedule.
- server responds with a 200 if request was successfulll
- its poosible to get data for a custom date. If the date is not passed then server retrievs the current data.
    

``` json
{
    "suggested_activites": [
        {
            "id": 1,
            "name": "Studying"
        },
        {
            "id": 2,
            "name": "Physical Training"
        },
        {
            "id": 3,
            "name": "Creative Work"
        },
        {
            "id": 4,
            "name": "Social"
        },
        {
            "id": 5,
            "name": "Context Switch"
        }
    ],
    "suggested_sub_activites": [
        {
            "activity_id": 4,
            "attribute_weights": {
                "CHA": 0.8,
                "INT": 0.2
            },
            "base_exp": 80,
            "difficulty_multiplier": 1.2,
            "id": 12,
            "name": "Networking",
            "scheduled_time": 60
        },
        {
            "activity_id": 5,
            "attribute_weights": {},
            "base_exp": 0,
            "difficulty_multiplier": 0.0,
            "id": 14,
            "name": "Short Break",
            "scheduled_time": 15
        },
        {
            "activity_id": 1,
            "attribute_weights": {
                "DSC": 0.1,
                "FCS": 0.2,
                "INT": 0.7
            },
            "base_exp": 200,
            "difficulty_multiplier": 1.8,
            "id": 4,
            "name": "Computer Science",
            "scheduled_time": 120
        },
        {
            "activity_id": 1,
            "attribute_weights": {
                "DSC": 0.1,
                "FCS": 0.2,
                "INT": 0.7
            },
            "base_exp": 200,
            "difficulty_multiplier": 1.8,
            "id": 4,
            "name": "Computer Science",
            "scheduled_time": 120
        },
        {
            "activity_id": 5,
            "attribute_weights": {},
            "base_exp": 0,
            "difficulty_multiplier": 0.0,
            "id": 15,
            "name": "Long Break",
            "scheduled_time": 30
        },
        {
            "activity_id": 2,
            "attribute_weights": {
                "DSC": 0.2,
                "STA": 0.8
            },
            "base_exp": 90,
            "difficulty_multiplier": 1.4,
            "id": 7,
            "name": "Running",
            "scheduled_time": 45
        },
        {
            "activity_id": 5,
            "attribute_weights": {},
            "base_exp": 0,
            "difficulty_multiplier": 0.0,
            "id": 14,
            "name": "Short Break",
            "scheduled_time": 15
        },
        {
            "activity_id": 3,
            "attribute_weights": {
                "CHA": 0.5,
                "FCS": 0.1,
                "INT": 0.4
            },
            "base_exp": 180,
            "difficulty_multiplier": 1.6,
            "id": 10,
            "name": "Digital Art",
            "scheduled_time": 120
        },
        {
            "activity_id": 3,
            "attribute_weights": {
                "CHA": 0.5,
                "FCS": 0.1,
                "INT": 0.4
            },
            "base_exp": 180,
            "difficulty_multiplier": 1.6,
            "id": 10,
            "name": "Digital Art",
            "scheduled_time": 120
        },
        {
            "activity_id": 5,
            "attribute_weights": {},
            "base_exp": 0,
            "difficulty_multiplier": 0.0,
            "id": 14,
            "name": "Short Break",
            "scheduled_time": 15
        },
        {
            "activity_id": 4,
            "attribute_weights": {
                "CHA": 0.6,
                "DSC": 0.4
            },
            "base_exp": 100,
            "difficulty_multiplier": 1.3,
            "id": 13,
            "name": "Team Collaboration",
            "scheduled_time": 90
        },
        {
            "activity_id": 5,
            "attribute_weights": {},
            "base_exp": 0,
            "difficulty_multiplier": 0.0,
            "id": 14,
            "name": "Short Break",
            "scheduled_time": 15
        }
    ]
}

 ```

- server with throuh an error if the date argument is not set correctly.
    

```
{
    "description": "InvalidRequestData('Date string must mactch %Y-%m-%d')",
    "msg": "Date string must mactch %Y-%m-%d",
    "type": "InvalidRequestData"
}

 ```


***Endpoint:***

```bash
Method: GET
Type: 
URL: {{port-500}}/api/timetable/scheduling/tasks
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |
| date | 2024-09-10 |  |



***More example Requests/Responses:***


#### I. Example Request: get tasks to schedule



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |
| date | 2024-09-10 |  |



***Body: None***



#### I. Example Response: get tasks to schedule
```js
{
    "new_activities": [],
    "suggested_activities": [
        {
            "id": 3,
            "name": "Daily Workout"
        },
        {
            "id": 4,
            "name": "Context switch"
        },
        {
            "id": 5,
            "name": "Context switch"
        }
    ],
    "suggested_sub_activities": [
        {
            "activity_id": 3,
            "attribute_weights": {
                "DSC": 0.2,
                "FCS": 0.3,
                "STA": 0.5
            },
            "base_exp": 80,
            "difficulty_multiplier": 1,
            "id": 3,
            "name": "Morning Cycling",
            "scheduled_time": 45
        },
        {
            "activity_id": 5,
            "attribute_weights": {},
            "base_exp": 0,
            "difficulty_multiplier": 1,
            "id": 5,
            "name": "Short Break",
            "scheduled_time": 15
        }
    ]
}
```


***Status Code:*** 200

<br>



## stats

Retrieve statitcs about the current user.



### 1. get user's stats



***Endpoint:***

```bash
Method: GET
Type: 
URL: {{port-500}}/api/stats
```



***Query params:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***More example Requests/Responses:***


#### I. Example Request: get user's stats



***Query:***

| Key | Value | Description |
| --- | ------|-------------|
| tkn | {{testing-rpg-tkn}} |  |



***Body: None***



#### I. Example Response: get user's stats
```js
{
    "completion_history": {},
    "discipline_factor": 0,
    "level_progress": {
        "current_exp": 46,
        "current_level": 1,
        "max_level": true
    },
    "user": {
        "attributes": {
            "CHA": 0,
            "DSC": 12,
            "FCS": 16,
            "INT": 0,
            "STA": 30
        },
        "id": 2,
        "level": 1,
        "total_exp": 46,
        "username": "test"
    }
}
```


***Status Code:*** 200

<br>



---
[Back to top](#rpg-system)

>Generated at 2025-05-23 17:24:02 by [docgen](https://github.com/thedevsaddam/docgen)
