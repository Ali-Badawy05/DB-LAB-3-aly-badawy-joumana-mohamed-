USE company;

INSERT INTO employee (ssn, fname, lname, bdate, address, gender, salary, Dno) VALUES
    ('123456789', 'Ahmed',   'Hassan',  '1990-01-09', 'Smouha, Alexandria',     'M', 30000.00, NULL),
    ('333445555', 'Mona',    'Samir',   '1985-12-08', 'Nasr City, Cairo',       'F', 40000.00, NULL),
    ('999887777', 'Omar',    'Khaled',  '1992-07-19', 'Sidi Gaber, Alexandria', 'M', 25000.00, NULL),
    ('987654321', 'Sara',    'Mostafa', '1988-06-20', 'Maadi, Cairo',           'F', 43000.00, NULL),
    ('666884444', 'Youssef', 'Nabil',   '1995-09-15', 'Mansoura',               'M', 38000.00, NULL),
    ('888665555', 'Laila',   'Adel',    '1978-11-10', 'Giza',                   'F', 55000.00, NULL);

INSERT INTO department (Dnumber, Dname, mgr_ssn, mgr_start_date) VALUES
    (1, 'Research',       '333445555', '2020-05-22'),
    (2, 'Administration', '987654321', '2021-01-01'),
    (3, 'Headquarters',   '888665555', '2019-06-19');

UPDATE employee SET Dno = 1 WHERE ssn IN ('123456789', '333445555');
UPDATE employee SET Dno = 2 WHERE ssn IN ('999887777', '987654321');
UPDATE employee SET Dno = 3 WHERE ssn IN ('666884444', '888665555');


INSERT INTO project (Pnumber, Pname, Plocation, Dno) VALUES
    (1, 'ProductX',        'Alexandria', 1),
    (2, 'ProductY',        'Cairo',      1),
    (3, 'Computerization', 'Cairo',      2),
    (4, 'Reorganization',  'Giza',       3);
