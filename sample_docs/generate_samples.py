import os
from pathlib import Path
import pymupdf as fitz

sample_dir = Path("sample_docs")
sample_dir.mkdir(parents=True, exist_ok=True)

# 1. Valid Mid Exam Question Paper
doc1 = fitz.open()
p1 = doc1.new_page()
t1 = """ANANTHA LAKSHMI INSTITUTE OF TECHNOLOGY AND SCIENCES
(Autonomous Institution - Accredited by NAAC with 'A' Grade)
B.Tech III Year I Semester Mid-I Examination
Department of Computer Science & Engineering
Subject: Database Management Systems | Subject Code: CS302 | Branch: CSE
Time: 2 Hours                                            Maximum Marks: 70

PART A (Compulsory - 5 x 2 = 10 Marks)
1. Define primary key and foreign key with a real-world example. [2 marks]
2. What is the difference between DDL and DML commands in SQL? [2 marks]
3. State the ACID properties of database transactions. [2 marks]
4. Define functional dependency and trivial functional dependency. [2 marks]
5. What is the role of the Database Administrator (DBA)? [2 marks]

PART B (Answer all questions, 6 x 10 = 60 Marks)
1. Explain the Three-Schema Architecture of DBMS with a neat diagram. [10 marks]
2. Construct an Entity-Relationship (ER) diagram for a University Management System. [10 marks]
3. Explain Relational Algebra operations with appropriate SQL equivalents. [10 marks]
4. Discuss First, Second, and Third Normal Forms (1NF, 2NF, 3NF) with sample relations. [10 marks]
5. Explain Two-Phase Locking (2PL) protocol for concurrency control. [10 marks]
6. Describe B-Tree and B+ Tree indexing techniques and their advantages. [10 marks]

*** End of Question Paper - Confidential Institutional Record ***
"""
p1.insert_textbox(fitz.Rect(50, 40, 550, 800), t1, fontsize=10, fontname="helv")
doc1.save(str(sample_dir / "Sample_Mid_Question_Paper_Valid.pdf"))
doc1.close()

# 2. Defective Mid Exam Question Paper (Missing Part B completely)
doc2 = fitz.open()
p2 = doc2.new_page()
t2 = """ANANTHA LAKSHMI INSTITUTE OF TECHNOLOGY AND SCIENCES
B.Tech III Year I Semester Mid-I Examination
Department of Computer Science & Engineering
Subject: Database Management Systems | Subject Code: CS302
Time: 2 Hours                                            Maximum Marks: 70

PART A (Answer all questions)
1. Define primary key and foreign key. [2 marks]
2. State the ACID properties. [2 marks]

*** End of Question Paper ***
"""
p2.insert_textbox(fitz.Rect(50, 40, 550, 800), t2, fontsize=10, fontname="helv")
doc2.save(str(sample_dir / "Sample_Question_Paper_Defective.pdf"))
doc2.close()

# 3. Valid Course Structure
doc3 = fitz.open()
p3 = doc3.new_page()
t3 = """ANANTHA LAKSHMI INSTITUTE OF TECHNOLOGY AND SCIENCES
Course Structure and Syllabus
Programme: B.Tech Computer Science & Engineering
Course Name: Operating Systems
Course Code: CS304 | Credits: 3

Unit 1: Introduction to Operating Systems
Unit 1 Topics: Evolution of operating systems, system calls, OS structures, process concepts, process scheduling, inter-process communication.

Unit 2: Process Synchronization and Deadlocks
Unit 2 Topics: Critical section problem, Peterson solution, semaphores, monitors, classic synchronization problems, deadlock characterization, deadlock prevention and avoidance.

Unit 3: Memory Management
Unit 3 Topics: Swapping, contiguous memory allocation, paging, segmentation, virtual memory, demand paging, page replacement algorithms.

Unit 4: Storage and File Systems
Unit 4 Topics: File concept, access methods, directory structure, disk structure, disk scheduling algorithms (FCFS, SSTF, SCAN, C-SCAN).

Unit 5: Protection and Security
Unit 5 Topics: Goals of protection, access matrix, authentication, program threats, system threats, cryptography as a security tool.

Reference Text Books:
1. Operating System Concepts - Silberschatz, Galvin, Gagne.
"""
p3.insert_textbox(fitz.Rect(50, 40, 550, 800), t3, fontsize=10, fontname="helv")
doc3.save(str(sample_dir / "Sample_Course_Structure_Valid.pdf"))
doc3.close()

print("Sample test PDFs generated successfully in sample_docs/ directory!")
