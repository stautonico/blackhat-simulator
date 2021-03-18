CREATE TABLE IF NOT EXISTS computer
(
    id text
);

CREATE TABLE IF NOT EXISTS blackhat_group
(
    id          integer PRIMARY KEY AUTOINCREMENT,
    gid         integer,
    name        text,
    computer_id text
);

CREATE TABLE IF NOT EXISTS group_membership
(
    id          integer PRIMARY KEY AUTOINCREMENT,
    computer_id text,
    user_uid    integer,
    group_gid   integer
);

CREATE TABLE IF NOT EXISTS blackhat_user
(
    id          integer PRIMARY KEY AUTOINCREMENT,
    uid         integer,
    username    text,
    password    text,
    full_name   text,
    room_number text,
    work_phone  text,
    home_phone  text,
    other       text,
    computer_id text
);