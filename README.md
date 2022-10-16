# API Specification

## GET `/plants/`

Return a paginated list with the registered plants.

Example response:

````json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "plant-1"
    },
    {
      "id": 2,
      "name": "plant-2"
    }
  ]
}
````

Status codes:

- 200: Successful response

## POST `/plants/`

Create a new plant.

Parameters:

- `name`: Plant name.

Example request:

````json
{
  "name": "plant-1"
}
````

Status codes:

- 201: Plant successfully created
- 400: Incorrect plant data

## GET `/plants/<id>/`

Return details for the given plant id.

Example response:

````json
{
  "id": 1,
  "name": "plant-1"
}
````

Status codes:

- 200: Successful response

## PATCH `/plants/<id>/`

Update details for the given plant id.

Example request:

````json
{
  "name": "plant-2"
}
````

Status codes:

- 200: Plant successfully updated
- 400: Incorrect plant data
- 404: No plant found with the ID provided

## DELETE `/plants/<id>/`

Delete the plant with the given id.

Status codes:

- 204: Plant successfully deleted
- 404: No plant found with the ID provided

## POST `/plants/pull_datapoints/`

Manually request to pull data from the monitoring service.

Parameters:

- `plant_ids`: (Optional) List with plant IDs to pull datapoints for. Defaults to all plant IDs.
- `from`: (Optional) Start date. Defaults to next date with no datapoints registered for each plant.
- `to`: (Optional) End date. Defaults to today.

Status codes:

- 200: Successful response
- 400: Incorrect filtering parameters

## GET `/plants/report/`

Return a report with plants details and their corresponding datapoints.

Parameters:

- `plant_ids`: (Optional) List with plant IDs to include in report. Defaults to all plant IDs.
- `from`: (Optional) Start date.
- `to`: (Optional) End date.

Example response:

````json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "plant-1",
      "datapoints": [
        {
          "timestamp": "2022-01-01T00:00:00Z",
          "energy_expected": 25.932926082137755,
          "energy_observed": 84.51788208660457,
          "irradiation_expected": 61.51016754434042,
          "irradiation_observed": 46.50320357480399
        },
        {
          "timestamp": "2022-01-01T01:00:00Z",
          "energy_expected": 87.06914261163489,
          "energy_observed": 56.72031459453898,
          "irradiation_expected": 73.98168981423716,
          "irradiation_observed": 48.03161135428289
        }
      ]
    }
  ]
}
````

Status codes:

- 200: Successful response
- 400: Incorrect filtering parameters