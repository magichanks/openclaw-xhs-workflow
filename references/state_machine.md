# State Machine

Recommended main workflow states:

```text
created
-> researched
-> drafted
-> imaged
-> reviewed
-> ready_to_fill
-> filled
-> published
```

Side states:

- `failed`
- `blocked`

## Rule

Main state describes where the workflow is.
Sub-status fields describe how each content, image, review, and publisher stage ended.
