create table two_cams (
	id  		serial primary key,
	Filename 	varchar(100),
	device_id 	varchar(50),
	image_path	text,
	side 		varchar(10) default '',
	lat 		float default 0,
	long		float default 0,
	captured_at	timestamp default now(),
	received_at	timestamp default now(),
	label		varchar(100) default ''
);
