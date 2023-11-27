import jaydebeapi
import io

# Replace these placeholders with your actual connection details
database_url = "jdbc:tibero:thin:@jamong-dock:9440:TAC"
username = "sys"
password = "tibero"
jdbc_driver_jar = "/client/lib/jar/tibero7-jdbc.jar"  # Path to the Tibero JDBC driver JAR file


#replace as your preference
image_path = "./000.jpg"
image_label = 1

# Read the image file and convert it to a byte array
with open(image_path, "rb") as image_file:
    image_data = image_file.read()

try:
    # Establish the JDBC connection
    jdbc_connection = jaydebeapi.connect(
        "com.tmax.tibero.jdbc.TbDriver",
        database_url,
        [username, password],
        jdbc_driver_jar,
    )

    # Create a cursor
    cursor = jdbc_connection.cursor()

    try:
        # Create a sequence for generating unique IDs
        create_sequence_query = "CREATE SEQUENCE my_sequence"
        cursor.execute(create_sequence_query)

        # Commit the transaction
        jdbc_connection.jconn.commit()

        print("Sequence 'my_sequence' created successfully.")

        # Example SQL query to create a table for image data
        create_table_query = """
        CREATE TABLE my_table (
            id NUMBER DEFAULT my_sequence.NEXTVAL PRIMARY KEY,
            image_name VARCHAR(255) NOT NULL,
            image_data BLOB,
            image_label int NOT NULL,
        )
        """
        cursor.execute(create_table_query)

        # Commit the transaction
        jdbc_connection.jconn.commit()

        print("Table 'my_table' created successfully.")

        # Example SQL query to insert image data into the table
        insert_image_query = "INSERT INTO my_table (image_name, image_data, image_label) VALUES (?, TO_BLOB(?), ?)"
        image_name = "000.jpg"
        # Execute the insert image query with image name and data as parameters
        cursor.execute(insert_image_query, [image_name, image_data, image_label])

        # Commit the transaction
        jdbc_connection.jconn.commit()

        print(f"Image data for '{image_name}' inserted successfully.")

    except Exception as table_creation_error:
        # Handle table creation error
        print(f"Error creating table or inserting image data. Error: {table_creation_error}")

        # Attempt to drop the sequence and table on error
        try:
            drop_sequence_query = "DROP SEQUENCE my_sequence"
            cursor.execute(drop_sequence_query)
            jdbc_connection.jconn.commit()
            print("Sequence 'my_sequence' dropped successfully.")
        except Exception as drop_sequence_error:
            print(f"Failed to drop sequence. Error: {drop_sequence_error}")

        try:
            drop_table_query = "DROP TABLE my_table"
            cursor.execute(drop_table_query)
            jdbc_connection.jconn.commit()
            print("Table 'my_table' dropped successfully.")
        except Exception as drop_table_error:
            print(f"Failed to drop table. Error: {drop_table_error}")

except Exception as connection_error:
    # Handle the connection error
    print(f"Failed to connect to the database. Error: {connection_error}")

finally:
    # Close the cursor and JDBC connection when done (if they were established)
    if 'cursor' in locals():
        cursor.close()

    if 'jdbc_connection' in locals():
        jdbc_connection.close()
