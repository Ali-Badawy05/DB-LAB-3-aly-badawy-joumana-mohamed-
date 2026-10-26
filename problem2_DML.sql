USE library;

INSERT INTO author (author_id, name, country) VALUES
    (1, 'Naguib Mahfouz',          'Egypt'),
    (2, 'Agatha Christie',         'United Kingdom'),
    (3, 'Gabriel Garcia Marquez',  'Colombia'),
    (4, 'Haruki Murakami',         'Japan');

INSERT INTO book (book_id, title, price, author_id) VALUES
    (1, 'Palace Walk',                        14.50, 1),
    (2, 'Midaq Alley',                        12.00, 1),
    (3, 'Murder on the Orient Express',       10.99, 2),
    (4, 'And Then There Were None',            9.75, 2),
    (5, 'One Hundred Years of Solitude',      16.20, 3),
    (6, 'Love in the Time of Cholera',        15.40, 3),
    (7, 'Norwegian Wood',                     13.30, 4),
    (8, 'Kafka on the Shore',                 17.80, 4);
