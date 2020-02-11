drop table requests;
drop table users;

create table users
(
	id integer
		constraint users_pk
			primary key,
	full_name varchar,
	created datetime
);

create table requests
(
	user_id integer
		references users,
	region varchar,
	text_request varchar,
	file_name varchar,
	status integer,
	created datetime,
	updated datetime,
	vacancy_number integer,
	id integer
		constraint requests_pk
			primary key autoincrement
);

