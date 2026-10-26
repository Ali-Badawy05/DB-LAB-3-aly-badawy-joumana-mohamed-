Lab 3 - Problem 1 (COMPANY database) - Answers
==============================================
Database built with:  mysql -u root -p < problem1_DDL.sql   and   mysql -u root -p < problem1_DML.sql
Every statement below was typed in the MySQL client:  mysql -u root -p company


----------------------------------------------------------------------
Q1.1  Insert a row in DEPARTMENT that references a row in EMPLOYEE.
      Then try to delete the referenced row. What will happen?
----------------------------------------------------------------------
SQL used:

mysql> INSERT INTO employee (ssn, fname, lname, bdate, address, gender, salary, Dno)
    -> VALUES ('900000001', 'Hany', 'Fathy', '1991-04-04', 'Alexandria', 'M', 28000.00, 1);
Query OK, 1 row affected

mysql> INSERT INTO department (Dnumber, Dname, mgr_ssn, mgr_start_date)
    -> VALUES (9, 'Quality', '900000001', '2026-01-01');
Query OK, 1 row affected

mysql> SELECT * FROM department WHERE Dnumber = 9;
+---------+---------+-----------+----------------+
| Dnumber | Dname   | mgr_ssn   | mgr_start_date |
+---------+---------+-----------+----------------+
|       9 | Quality | 900000001 | 2026-01-01     |
+---------+---------+-----------+----------------+
1 row in set

mysql> DELETE FROM employee WHERE ssn = '900000001';
ERROR 1451 (23000): Cannot delete or update a parent row: a foreign key constraint fails (`company`.`department`, CONSTRAINT `fk_dept_mgr` FOREIGN KEY (`mgr_ssn`) REFERENCES `employee` (`ssn`))

mysql> SELECT ssn, fname, lname FROM employee WHERE ssn = '900000001';
+-----------+-------+-------+
| ssn       | fname | lname |
+-----------+-------+-------+
| 900000001 | Hany  | Fathy |
+-----------+-------+-------+
1 row in set

Answer: MySQL REJECTS the DELETE with error 1451. The employee is the manager of department 9
(department.mgr_ssn points to him), so deleting him would leave a foreign key value with no
matching primary key. This is referential integrity. The employee row is still there.
To delete him we must first remove (or change) the department row that references him:

mysql> DELETE FROM department WHERE Dnumber = 9;
Query OK, 1 row affected

mysql> DELETE FROM employee WHERE ssn = '900000001';
Query OK, 1 row affected
(this last part only cleans the test rows, so the sample data stays as it was)


----------------------------------------------------------------------
Q1.2  Insert a row in PROJECT that references a DEPARTMENT that doesn't exist yet.
      What will happen?
----------------------------------------------------------------------
SQL used (there is no department with Dnumber 77):

mysql> INSERT INTO project (Pnumber, Pname, Plocation, Dno)
    -> VALUES (99, 'NewProject', 'Cairo', 77);
ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails (`company`.`project`, CONSTRAINT `fk_proj_dept` FOREIGN KEY (`Dno`) REFERENCES `department` (`Dnumber`))

mysql> SELECT * FROM project WHERE Pnumber = 99;
Empty set

Answer: MySQL REJECTS the INSERT with error 1452. A foreign key value must be NULL or equal to an
existing primary key value of the referenced table. Department 77 does not exist, so nothing is
inserted. (project.Dno is NOT NULL, so NULL is not allowed either.) The department must be
inserted first, and then the project.


----------------------------------------------------------------------
Q1.3  If mgr_ssn and Dno are both NOT NULL, how will you insert the first row
      in EMPLOYEE or DEPARTMENT?
----------------------------------------------------------------------
The two foreign keys point to each other (employee.Dno -> department.Dnumber and
department.mgr_ssn -> employee.ssn). To try it without touching the real data I used a separate
database, company_q13, with both columns NOT NULL:

mysql> CREATE DATABASE company_q13;
mysql> USE company_q13;
mysql> CREATE TABLE employee (ssn CHAR(9) NOT NULL, fname VARCHAR(30) NOT NULL,
    ->   lname VARCHAR(30) NOT NULL, bdate DATE, address VARCHAR(100), gender CHAR(1),
    ->   salary DECIMAL(10,2), Dno INT NOT NULL, PRIMARY KEY (ssn));
Query OK, 0 rows affected

mysql> CREATE TABLE department (Dnumber INT NOT NULL, Dname VARCHAR(50) NOT NULL,
    ->   mgr_ssn CHAR(9) NOT NULL, mgr_start_date DATE, PRIMARY KEY (Dnumber),
    ->   FOREIGN KEY (mgr_ssn) REFERENCES employee (ssn));
Query OK, 0 rows affected

mysql> ALTER TABLE employee ADD FOREIGN KEY (Dno) REFERENCES department (Dnumber);
Query OK, 0 rows affected

Try 1: the employee first.

mysql> INSERT INTO employee (ssn, fname, lname, bdate, address, gender, salary, Dno)
    -> VALUES ('111111111', 'Ali', 'Gamal', '1980-01-01', 'Cairo', 'M', 50000.00, 1);
ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails (`company_q13`.`employee`, CONSTRAINT `employee_ibfk_1` FOREIGN KEY (`Dno`) REFERENCES `department` (`Dnumber`))

Try 2: the department first.

mysql> INSERT INTO department (Dnumber, Dname, mgr_ssn, mgr_start_date)
    -> VALUES (1, 'Research', '111111111', '2020-01-01');
ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails (`company_q13`.`department`, CONSTRAINT `department_ibfk_1` FOREIGN KEY (`mgr_ssn`) REFERENCES `employee` (`ssn`))

Both fail: the employee needs the department to exist, and the department needs the employee to
exist. NULL is not allowed, so we cannot insert one of them with an empty foreign key and fix it
later. The way out is to switch the foreign key check off for a moment, insert the two rows, and
switch it on again:

mysql> SET FOREIGN_KEY_CHECKS = 0;
Query OK, 0 rows affected

mysql> INSERT INTO employee (ssn, fname, lname, bdate, address, gender, salary, Dno)
    -> VALUES ('111111111', 'Ali', 'Gamal', '1980-01-01', 'Cairo', 'M', 50000.00, 1);
Query OK, 1 row affected

mysql> INSERT INTO department (Dnumber, Dname, mgr_ssn, mgr_start_date)
    -> VALUES (1, 'Research', '111111111', '2020-01-01');
Query OK, 1 row affected

mysql> SET FOREIGN_KEY_CHECKS = 1;
Query OK, 0 rows affected

mysql> SELECT ssn, fname, Dno FROM employee;
+-----------+-------+-----+
| ssn       | fname | Dno |
+-----------+-------+-----+
| 111111111 | Ali   |   1 |
+-----------+-------+-----+
1 row in set

mysql> SELECT Dnumber, Dname, mgr_ssn FROM department;
+---------+----------+-----------+
| Dnumber | Dname    | mgr_ssn   |
+---------+----------+-----------+
|       1 | Research | 111111111 |
+---------+----------+-----------+
1 row in set

Answer: with both columns NOT NULL the first row can only be inserted with
SET FOREIGN_KEY_CHECKS = 0 (insert both rows, then SET FOREIGN_KEY_CHECKS = 1). The two rows
reference each other correctly, so the database is consistent after the check is switched on again.

The normal solution (the one used in problem1_DDL.sql and problem1_DML.sql) is to allow NULL in
one of the two columns: insert the employees with Dno = NULL, then the departments (their manager
already exists), then UPDATE employee SET Dno = ... to give the employees their department.

mysql> DROP DATABASE company_q13;     -- test database removed
