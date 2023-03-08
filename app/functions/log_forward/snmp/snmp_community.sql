create table snmp_community
(
    id                int auto_increment
        primary key,
    enable            int null,
    community_version int null,
    community_name    varchar(255) null,
    community_hosts   mediumtext null,
    security_level    mediumtext null,
    queries           mediumtext null,
    traps             mediumtext null,
    snmp_events       mediumtext null,
    constraint snmp_community_community_name_uindex
        unique (community_name)
);