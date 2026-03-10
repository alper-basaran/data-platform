with source_data as (
    select
        change_id,
        revision_id_old,
        revision_id_new,
        nullif(trim(title), '') as page_title,
        event_timestamp,
        nullif(trim(username), '') as username,
        nullif(trim(comment), '') as event_comment,
        old_length,
        new_length,
        (coalesce(new_length, 0) - coalesce(old_length, 0))::integer as length_delta,
        nullif(trim(log_type), '') as log_type,
        nullif(trim(log_action), '') as log_action
    from {{ source('wikipedia', 'wikipedia_page_events') }}
)

select
    change_id,
    revision_id_old,
    revision_id_new,
    page_title,
    event_timestamp,
    date_trunc('day', event_timestamp)::date as event_date,
    date_trunc('hour', event_timestamp) as event_hour,
    username,
    (username is null) as is_anonymous,
    event_comment,
    old_length,
    new_length,
    length_delta,
    log_type,
    log_action
from source_data
where change_id is not null
