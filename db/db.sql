CREATE TABLE users (
    name varchar PRIMARY KEY,
    password varchar NOT NULL
);

CREATE TABLE targets (
    uuid varchar PRIMARY KEY,
    name varchar NOT NULL,
    hosts varchar NOT NULL,
    owner varchar REFERENCES users(name) NOT NULL,
    CONSTRAINT targets_name_owner UNIQUE (name, owner)
);

CREATE TABLE tasks (
    uuid varchar PRIMARY KEY,
    name varchar NOT NULL,
    owner varchar REFERENCES users(name) NOT NULL,
    target varchar REFERENCES targets(uuid) NOT NULL,
    CONSTRAINT tasks_name_owner UNIQUE (name, owner)
);

CREATE TABLE reports (
    uuid varchar PRIMARY KEY,
    owner varchar REFERENCES users(name) NOT NULL,
    task varchar REFERENCES tasks(uuid) NOT NULL,
    time timestamp NOT NULL
);
