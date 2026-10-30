import sys
from pathlib import Path
sys.path.insert(0, ".")

from backend.database import get_db_cursor
from backend.services.auth_service import hash_password

INSTITUTION_ID = 6

DEPARTMENTS = [
    {"code": "CSE", "name": "Computer Science & Engineering"},
    {"code": "CSD", "name": "Computer Science & Design"},
    {"code": "CSM", "name": "Computer Science & Machine Learning"},
    {"code": "CSE-AIML", "name": "Computer Science & Engineering (Artificial Intelligence & Machine Learning)"},
    {"code": "CAI", "name": "Computer Artificial Intelligence"},
    {"code": "ECE", "name": "Electronics & Communication Engineering"},
    {"code": "EEE", "name": "Electrical & Electronics Engineering"},
    {"code": "ME", "name": "Mechanical Engineering"},
    {"code": "CE", "name": "Civil Engineering"},
]

COMMON_1_1 = [
    ("BS1101", "Linear Algebra & Calculus", 4),
    ("BS1102", "Engineering Physics", 3),
    ("ES1101", "Introduction to Programming Using C", 3),
    ("ES1102", "Basic Electrical & Electronics Engineering", 3),
    ("ES1103", "Engineering Graphics / Drawing", 3),
    ("HS1101", "Communicative English", 2),
    ("BS1102L", "Engineering Physics / Chemistry Lab", 1.5),
    ("ES1101L", "Computer Programming Using C Lab", 1.5),
    ("ES1104L", "IT Workshop & Engineering Practices Lab", 1.5),
    ("ES1102L", "Basic Electrical & Electronics Engineering Lab", 1.5),
]

COMMON_1_2 = [
    ("BS1201", "Differential Equations & Vector Calculus", 4),
    ("BS1202", "Engineering Chemistry", 3),
    ("ES1201", "Engineering Mechanics", 3),
    ("ES1202", "Data Structures", 3),
    ("ES1203", "Basic Civil & Mechanical Engineering Systems", 3),
    ("ES1202L", "Data Structures Lab", 1.5),
    ("ES1204L", "Engineering & IT Workshop Lab", 1.5),
    ("HS1201L", "English Communication Skills Lab", 1.5),
]

BRANCH_CURRICULUM = {
    "CSE": {
        3: [
            ("CS2101", "Mathematical Foundations of Computer Science (Discrete Mathematics)", 3),
            ("CS2102", "Digital Electronics & Logic Design", 3),
            ("CS2103", "Object-Oriented Programming through Java", 3),
            ("CS2104", "Database Management Systems (DBMS)", 3),
            ("CS2105", "Computer Organization & Architecture", 3),
            ("CS2103L", "Java Programming Lab", 1.5),
            ("CS2104L", "DBMS Lab", 1.5),
            ("CS2102L", "Logic Design Lab", 1.5),
        ],
        4: [
            ("CS2201", "Probability and Statistics", 3),
            ("CS2202", "Operating Systems", 3),
            ("CS2203", "Formal Languages & Automata Theory", 3),
            ("CS2204", "Design and Analysis of Algorithms", 3),
            ("CS2205", "Software Engineering", 3),
            ("CS2202L", "Operating Systems Lab", 1.5),
            ("CS2205L", "Software Engineering Lab", 1.5),
            ("CS2206L", "R Programming & Web Development Lab", 1.5),
        ],
        5: [
            ("CS3101", "Computer Networks", 3),
            ("CS3102", "Compiler Design", 3),
            ("CS3103", "Artificial Intelligence", 3),
            ("CS3104", "Professional Elective I (Data Science / Cloud Computing / Cyber Security)", 3),
            ("OE3101", "Open Elective I (Humanities / Management)", 3),
            ("CS3101L", "Computer Networks & Compiler Design Lab", 1.5),
            ("CS3103L", "Advanced Python / AI Lab", 1.5),
            ("HS3101L", "Soft Skills & Employability Training", 1),
        ],
        6: [
            ("CS3201", "Machine Learning", 3),
            ("CS3202", "Cryptography & Network Security", 3),
            ("CS3203", "Object Oriented Analysis and Design (OOAD)", 3),
            ("CS3204", "Professional Elective II (Big Data Analytics / Mobile Application Development)", 3),
            ("OE3201", "Open Elective II (Interdisciplinary)", 3),
            ("CS3201L", "Machine Learning Lab", 1.5),
            ("CS3202L", "Cryptography & Network Security Lab", 1.5),
        ],
        7: [
            ("CS4101", "Cloud Computing & Virtualization", 3),
            ("CS4102", "Professional Elective III (Deep Learning / Internet of Things)", 3),
            ("CS4103", "Professional Elective IV (Block Chain Technology / DevOps)", 3),
            ("CS4104", "Professional Elective V (Natural Language Processing)", 3),
            ("OE4101", "Open Elective III", 3),
            ("CS4105P", "Industry Internships Evaluation", 2),
            ("CS4106P", "Technical Mini Project", 2),
        ],
        8: [
            ("CS4201P", "Major Project Work (Phase-II)", 8),
            ("CS4202S", "Full Semester Seminar & Industrial Internship Evaluation", 4),
        ]
    },
    "CSD": {
        3: [
            ("CD2101", "Mathematical Foundations of Computer Science", 3),
            ("CD2102", "Design Thinking & Innovation Principles", 3),
            ("CD2103", "Data Structures & Algorithm Design", 3),
            ("CD2104", "Computer Organization & Architecture", 3),
            ("CD2105", "Object Oriented Programming through Java", 3),
            ("CD2102L", "Design Studio & Prototyping Lab", 1.5),
            ("CD2105L", "Java & Algorithms Lab", 1.5),
        ],
        4: [
            ("CD2201", "Discrete Mathematics & Graph Theory", 3),
            ("CD2202", "Computer Graphics & Multimedia Systems", 3),
            ("CD2203", "Operating Systems", 3),
            ("CD2204", "Database Management Systems", 3),
            ("CD2205", "UI/UX Design Principles & Guidelines", 3),
            ("CD2205L", "UI/UX Wireframing & Design Lab", 1.5),
            ("CD2204L", "DBMS & SQL Lab", 1.5),
        ],
        5: [
            ("CD3101", "Full Stack Web Development", 3),
            ("CD3102", "Software Engineering with Agile Design", 3),
            ("CD3103", "Computer Networks", 3),
            ("CD3104", "Professional Elective I (Interaction Design / 2D-3D Animation)", 3),
            ("OE3101", "Open Elective I", 3),
            ("CD3101L", "Full Stack Web Development Lab", 1.5),
            ("CD3104L", "Interactive Media Design Lab", 1.5),
        ],
        6: [
            ("CD3201", "Visual Design & Visual Communication", 3),
            ("CD3202", "Mobile App UI/UX Development", 3),
            ("CD3203", "Machine Learning for Designers", 3),
            ("CD3204", "Professional Elective II (Augmented & Virtual Reality / Game Design)", 3),
            ("OE3201", "Open Elective II", 3),
            ("CD3204L", "AR / VR & Game Prototyping Lab", 1.5),
            ("CD3202L", "Mobile App UI Lab", 1.5),
        ],
        7: [
            ("CD4101", "Human Computer Interaction (HCI)", 3),
            ("CD4102", "Cloud Computing & Scalable Design", 3),
            ("CD4103", "Professional Elective III (Information Visualization / 3D Modeling)", 3),
            ("CD4104", "Professional Elective IV (Digital Product Management)", 3),
            ("OE4101", "Open Elective III", 3),
            ("CD4105P", "Design Mini Project & Industry Internship", 3),
        ],
        8: [
            ("CD4201P", "Major Project Work (Phase-II Design Capstone)", 8),
            ("CD4202S", "Full Semester Design Seminar & Defense", 4),
        ]
    },
    "CSM": {
        3: [
            ("CM2101", "Mathematical Foundations for Machine Learning", 3),
            ("CM2102", "Advanced Data Structures using Python", 3),
            ("CM2103", "Digital Logic & Computer Organization", 3),
            ("CM2104", "Python Programming for Data Science", 3),
            ("CM2105", "Object-Oriented Programming through Java", 3),
            ("CM2104L", "Python for Data Science Lab", 1.5),
            ("CM2102L", "Data Structures Lab", 1.5),
        ],
        4: [
            ("CM2201", "Probability & Inferential Statistics", 3),
            ("CM2202", "Database Management Systems", 3),
            ("CM2203", "Operating Systems", 3),
            ("CM2204", "Design and Analysis of Algorithms", 3),
            ("CM2205", "Artificial Intelligence Principles & Search", 3),
            ("CM2205L", "Artificial Intelligence Lab", 1.5),
            ("CM2202L", "Database Systems Lab", 1.5),
        ],
        5: [
            ("CM3101", "Machine Learning Algorithms", 3),
            ("CM3102", "Computer Networks", 3),
            ("CM3103", "Formal Languages & Compiler Design", 3),
            ("CM3104", "Professional Elective I (Data Mining & Warehousing / Big Data)", 3),
            ("OE3101", "Open Elective I", 3),
            ("CM3101L", "Machine Learning Lab", 1.5),
            ("CM3104L", "Big Data Analytics Lab", 1.5),
        ],
        6: [
            ("CM3201", "Deep Learning & Neural Networks", 3),
            ("CM3202", "Natural Language Processing", 3),
            ("CM3203", "Cryptography & Secure ML", 3),
            ("CM3204", "Professional Elective II (Computer Vision / Reinforcement Learning)", 3),
            ("OE3201", "Open Elective II", 3),
            ("CM3201L", "Deep Learning Lab (PyTorch / TensorFlow)", 1.5),
            ("CM3202L", "Natural Language Processing Lab", 1.5),
        ],
        7: [
            ("CM4101", "Generative AI & Large Language Models", 3),
            ("CM4102", "MLOps & Automated Pipeline Deployment", 3),
            ("CM4103", "Professional Elective III (Autonomous Robotics & Edge AI)", 3),
            ("CM4104", "Professional Elective IV (AI in Healthcare & Finance)", 3),
            ("OE4101", "Open Elective III", 3),
            ("CM4105P", "Machine Learning Mini Project & Internship", 3),
        ],
        8: [
            ("CM4201P", "Major Project Work Phase-II (ML Capstone)", 8),
            ("CM4202S", "Industry Internship Evaluation & Defense", 4),
        ]
    },
    "CSE-AIML": {
        3: [
            ("AI2101", "Discrete Mathematics & Linear Algebra for AI", 3),
            ("AI2102", "Data Structures & Algorithms in Python", 3),
            ("AI2103", "Digital Logic Design & Systems Architecture", 3),
            ("AI2104", "Object Oriented Design Principles", 3),
            ("AI2105", "Database Systems for Intelligent Applications", 3),
            ("AI2102L", "Data Structures & Python Lab", 1.5),
            ("AI2105L", "Database Systems Lab", 1.5),
        ],
        4: [
            ("AI2201", "Statistical Foundations & Probability for AI", 3),
            ("AI2202", "Artificial Intelligence & Expert Systems", 3),
            ("AI2203", "Operating Systems", 3),
            ("AI2204", "Design & Analysis of Algorithms", 3),
            ("AI2205", "Software Engineering Methodologies", 3),
            ("AI2202L", "AI Algorithms Lab", 1.5),
            ("AI2203L", "Operating Systems Lab", 1.5),
        ],
        5: [
            ("AI3101", "Machine Learning Core Concepts", 3),
            ("AI3102", "Knowledge Representation & Reasoning", 3),
            ("AI3103", "Computer Networks & Distributed Systems", 3),
            ("AI3104", "Professional Elective I (Cloud AI Services / Pattern Recognition)", 3),
            ("OE3101", "Open Elective I", 3),
            ("AI3101L", "Machine Learning Lab", 1.5),
            ("AI3102L", "Knowledge Engineering Lab", 1.5),
        ],
        6: [
            ("AI3201", "Deep Learning Architectures", 3),
            ("AI3202", "Natural Language Processing & Speech", 3),
            ("AI3203", "Computer Vision & Image Processing", 3),
            ("AI3204", "Professional Elective II (Reinforcement Learning / AI Ethics & Governance)", 3),
            ("OE3201", "Open Elective II", 3),
            ("AI3201L", "Deep Learning & Vision Lab", 1.5),
            ("AI3202L", "NLP & Speech Processing Lab", 1.5),
        ],
        7: [
            ("AI4101", "Autonomous Systems & Intelligent Robotics", 3),
            ("AI4102", "Generative AI & Transformer Models", 3),
            ("AI4103", "Professional Elective III (Edge AI & IoT / Bio-Inspired AI)", 3),
            ("AI4104", "Professional Elective IV (AI for Cybersecurity)", 3),
            ("OE4101", "Open Elective III", 3),
            ("AI4105P", "AI Mini Project & Industry Internship", 3),
        ],
        8: [
            ("AI4201P", "Major Project Work Phase-II (AI Capstone)", 8),
            ("AI4202S", "Full Semester AI Internship Evaluation & Seminar", 4),
        ]
    },
    "CAI": {
        3: [
            ("CI2101", "Mathematical Foundations of Artificial Intelligence", 3),
            ("CI2102", "Data Structures & Algorithmic Analysis", 3),
            ("CI2103", "Computer Organization & Architecture", 3),
            ("CI2104", "Object Oriented Programming using C++ / Python", 3),
            ("CI2105", "Principles of AI Systems", 3),
            ("CI2102L", "Data Structures Lab", 1.5),
            ("CI2105L", "AI Systems Prototyping Lab", 1.5),
        ],
        4: [
            ("CI2201", "Applied Probability & Stochastic Processes", 3),
            ("CI2202", "Relational Database Management Systems", 3),
            ("CI2203", "Modern Operating Systems", 3),
            ("CI2204", "Automata Theory & Computability", 3),
            ("CI2205", "Machine Learning Fundamentals", 3),
            ("CI2205L", "Machine Learning Lab", 1.5),
            ("CI2202L", "RDBMS Lab", 1.5),
        ],
        5: [
            ("CI3101", "Advanced Machine Learning & Optimization", 3),
            ("CI3102", "Data Communications & Computer Networks", 3),
            ("CI3103", "Computer Vision Fundamentals", 3),
            ("CI3104", "Professional Elective I (Cloud Platforms / Big Data Engineering)", 3),
            ("OE3101", "Open Elective I", 3),
            ("CI3101L", "Advanced ML Lab", 1.5),
            ("CI3103L", "Computer Vision Lab", 1.5),
        ],
        6: [
            ("CI3201", "Deep Neural Networks & Applications", 3),
            ("CI3202", "Natural Language Processing & Text Mining", 3),
            ("CI3203", "Cognitive Computing & Decision Support Systems", 3),
            ("CI3204", "Professional Elective II (Robotics / Semantic Web)", 3),
            ("OE3201", "Open Elective II", 3),
            ("CI3201L", "Deep Neural Networks Lab", 1.5),
            ("CI3202L", "NLP Lab", 1.5),
        ],
        7: [
            ("CI4101", "Generative AI Systems & Prompt Engineering", 3),
            ("CI4102", "Edge AI & Embedded Machine Learning", 3),
            ("CI4103", "Professional Elective III (Cyber-Physical Systems / AI Safety)", 3),
            ("CI4104", "Professional Elective IV (Quantum Computing & AI)", 3),
            ("OE4101", "Open Elective III", 3),
            ("CI4105P", "Applied AI Internship & Capstone Project", 3),
        ],
        8: [
            ("CI4201P", "Major Project Work Phase-II", 8),
            ("CI4202S", "Comprehensive Viva-Voce & Seminar", 4),
        ]
    },
    "ECE": {
        3: [
            ("EC2101", "Electronic Devices and Circuits", 3),
            ("EC2102", "Signals and Systems", 3),
            ("EC2103", "Network Analysis & Transmission Lines", 3),
            ("EC2104", "Digital Logic Design", 3),
            ("EC2105", "Random Variables & Stochastic Processes", 3),
            ("EC2101L", "Electronic Devices and Circuits Lab", 1.5),
            ("EC2102L", "Basic Simulation & Signals Lab", 1.5),
        ],
        4: [
            ("EC2201", "Analog Circuits", 3),
            ("EC2202", "Linear Control Systems", 3),
            ("EC2203", "Electromagnetic Waves and Transmission Lines", 3),
            ("EC2204", "Analog and Digital Communications", 3),
            ("EC2205", "Computer Architecture & Organization", 3),
            ("EC2201L", "Analog Circuits Lab", 1.5),
            ("EC2204L", "Analog & Digital Communications Lab", 1.5),
        ],
        5: [
            ("EC3101", "Linear Integrated Circuits & Applications", 3),
            ("EC3102", "Microprocessors and Microcontrollers", 3),
            ("EC3103", "Digital Signal Processing (DSP)", 3),
            ("EC3104", "Professional Elective I (VLSI Design / Embedded Systems)", 3),
            ("OE3101", "Open Elective I", 3),
            ("EC3102L", "Microprocessors and Microcontrollers Lab", 1.5),
            ("EC3101L", "Linear Integrated Circuits Lab", 1.5),
        ],
        6: [
            ("EC3201", "VLSI Design & Technology", 3),
            ("EC3202", "Microwave Engineering & Antenna Wave Propagation", 3),
            ("EC3203", "Digital Communication Systems", 3),
            ("EC3204", "Professional Elective II (Cellular Mobile Communications / Digital Image Processing)", 3),
            ("OE3201", "Open Elective II", 3),
            ("EC3201L", "VLSI & Microwave Engineering Lab", 1.5),
            ("EC3203L", "Digital Signal Processing Lab", 1.5),
        ],
        7: [
            ("EC4101", "Optical Communications & Photonics", 3),
            ("EC4102", "Professional Elective III (Embedded Systems / Real Time Operating Systems)", 3),
            ("EC4103", "Professional Elective IV (Radar Systems / Satellite Communications)", 3),
            ("EC4104", "Professional Elective V (CMOS Analog IC Design)", 3),
            ("OE4101", "Open Elective III", 3),
            ("EC4105P", "Industrial Training & Mini Project Evaluation", 3),
        ],
        8: [
            ("EC4201P", "Major Project Work Phase-II", 8),
            ("EC4202S", "Mandatory Industry Internship & Comprehensive Viva", 4),
        ]
    },
    "EEE": {
        3: [
            ("EE2101", "Electrical Circuit Analysis", 3),
            ("EE2102", "Electrical Machines - I", 3),
            ("EE2103", "Electromagnetic Fields", 3),
            ("EE2104", "Analog Electronics", 3),
            ("EE2105", "Power Systems - I (Generation & Transmission)", 3),
            ("EE2102L", "Electrical Machines Lab - I", 1.5),
            ("EE2104L", "Electronic Devices & Circuits Lab", 1.5),
        ],
        4: [
            ("EE2201", "Electrical Machines - II", 3),
            ("EE2202", "Control Systems", 3),
            ("EE2203", "Power Systems - II", 3),
            ("EE2204", "Digital Electronics & Logic Design", 3),
            ("EE2205", "Linear Integrated Circuits Applications", 3),
            ("EE2201L", "Electrical Machines Lab - II", 1.5),
            ("EE2202L", "Control Systems Lab", 1.5),
        ],
        5: [
            ("EE3101", "Power Electronics & Converters", 3),
            ("EE3102", "Microprocessors & Microcontrollers Architecture", 3),
            ("EE3103", "Power System Analysis", 3),
            ("EE3104", "Professional Elective I (Renewable Energy Systems / Electric Vehicles)", 3),
            ("OE3101", "Open Elective I", 3),
            ("EE3101L", "Power Electronics Lab", 1.5),
            ("EE3102L", "Microprocessors Lab", 1.5),
        ],
        6: [
            ("EE3201", "Power System Operation & Control", 3),
            ("EE3202", "Switchgear & Protection", 3),
            ("EE3203", "Electrical Measurements & Instrumentation", 3),
            ("EE3204", "Professional Elective II (High Voltage Engineering / Smart Grids)", 3),
            ("OE3201", "Open Elective II", 3),
            ("EE3203L", "Electrical Measurements Lab", 1.5),
            ("EE3201L", "Power Systems Simulation Lab", 1.5),
        ],
        7: [
            ("EE4101", "Utilization of Electrical Energy & Traction", 3),
            ("EE4102", "Professional Elective III (Flexible AC Transmission Systems / AI in Power)", 3),
            ("EE4103", "Professional Elective IV (Power Quality & Mitigation / Industrial Drives)", 3),
            ("EE4104", "Professional Elective V (Energy Auditing, Conservation & Management)", 3),
            ("OE4101", "Open Elective III", 3),
            ("EE4105P", "Industrial Internship & Mini Project", 3),
        ],
        8: [
            ("EE4201P", "Major Project Work Phase-II", 8),
            ("EE4202S", "Full Semester Industrial Internship Evaluation & Viva", 4),
        ]
    },
    "ME": {
        3: [
            ("ME2101", "Mechanics of Solids", 3),
            ("ME2102", "Metallurgy & Material Science", 3),
            ("ME2103", "Engineering Thermodynamics", 3),
            ("ME2104", "Manufacturing Technology", 3),
            ("ME2105", "Kinematics of Machinery", 3),
            ("ME2102L", "Material Science & Mechanics of Solids Lab", 1.5),
            ("ME2104L", "Manufacturing Technology Lab", 1.5),
        ],
        4: [
            ("ME2201", "Dynamics of Machinery", 3),
            ("ME2202", "Applied Thermodynamics - I", 3),
            ("ME2203", "Fluid Mechanics & Hydraulic Machines", 3),
            ("ME2204", "Machine Drawing & Computer Aided Drafting", 3),
            ("ME2205", "Instrumentation & Control Systems", 3),
            ("ME2203L", "Fluid Mechanics & Hydraulic Machinery Lab", 1.5),
            ("ME2204L", "Machine Tools & Production Lab", 1.5),
        ],
        5: [
            ("ME3101", "Applied Thermodynamics - II", 3),
            ("ME3102", "Design of Machine Elements - I", 3),
            ("ME3103", "Heat Transfer & Thermal Processes", 3),
            ("ME3104", "Metrology & Mechanical Measurements", 3),
            ("ME3105", "Professional Elective I (Automobile Engineering / Turbo Machinery)", 3),
            ("OE3101", "Open Elective I", 3),
            ("ME3103L", "Heat Transfer Lab", 1.5),
            ("ME3104L", "Metrology & Instrumentation Lab", 1.5),
        ],
        6: [
            ("ME3201", "Design of Machine Elements - II", 3),
            ("ME3202", "Operations Research & Industrial Management", 3),
            ("ME3203", "CAD / CAM (Computer Aided Design & Manufacturing)", 3),
            ("ME3204", "Professional Elective II (Robotics & Automation / Non-Destructive Testing)", 3),
            ("OE3201", "Open Elective II", 3),
            ("ME3203L", "CAD / CAM Lab", 1.5),
            ("ME3202L", "Simulation & Modeling Lab", 1.5),
        ],
        7: [
            ("ME4101", "Refrigeration & Air Conditioning Systems", 3),
            ("ME4102", "Finite Element Methods in Engineering", 3),
            ("ME4103", "Professional Elective III (Additive Manufacturing / Computational Fluid Dynamics)", 3),
            ("ME4104", "Professional Elective IV (Power Plant Engineering / Mechatronics)", 3),
            ("ME4105", "Professional Elective V (Total Quality Management & Six Sigma)", 3),
            ("OE4101", "Open Elective III", 3),
            ("ME4106P", "Industrial Internship / Technical Mini Project", 3),
        ],
        8: [
            ("ME4201P", "Major Project Work Phase-II (Manufacturing & Thermal Capstone)", 8),
            ("ME4202S", "Comprehensive Viva-Voce & Technical Seminar", 4),
        ]
    },
    "CE": {
        3: [
            ("CE2101", "Surveying & Geomatics", 3),
            ("CE2102", "Strength of Materials - I", 3),
            ("CE2103", "Fluid Mechanics", 3),
            ("CE2104", "Building Materials & Construction Practices", 3),
            ("CE2105", "Concrete Technology & Mix Design", 3),
            ("CE2101L", "Surveying Field Work Lab", 1.5),
            ("CE2102L", "Strength of Materials Lab", 1.5),
        ],
        4: [
            ("CE2201", "Strength of Materials - II", 3),
            ("CE2202", "Hydraulics & Hydraulic Machinery", 3),
            ("CE2203", "Structural Analysis - I", 3),
            ("CE2204", "Engineering Geology & Rock Mechanics", 3),
            ("CE2205", "Transportation Engineering - I (Highways)", 3),
            ("CE2202L", "Fluid Mechanics & Hydraulic Machinery Lab", 1.5),
            ("CE2205L", "Concrete Technology & Highway Lab", 1.5),
        ],
        5: [
            ("CE3101", "Structural Analysis - II", 3),
            ("CE3102", "Design of Reinforced Concrete Structures (Limit State)", 3),
            ("CE3103", "Geotechnical Engineering - I (Soil Mechanics)", 3),
            ("CE3104", "Hydrology & Water Resources Engineering", 3),
            ("CE3105", "Professional Elective I (Environmental Engineering / Advanced Surveying)", 3),
            ("OE3101", "Open Elective I", 3),
            ("CE3103L", "Geotechnical Engineering Lab", 1.5),
            ("CE3105L", "Transportation & Material Testing Lab", 1.5),
        ],
        6: [
            ("CE3201", "Design of Steel Structures (LSM)", 3),
            ("CE3202", "Geotechnical Engineering - II (Foundation Engineering)", 3),
            ("CE3203", "Environmental Engineering (Water & Wastewater)", 3),
            ("CE3204", "Transportation Engineering - II (Railways, Ports & Airports)", 3),
            ("CE3205", "Professional Elective II (Water Resources System Planning / Remote Sensing & GIS)", 3),
            ("OE3201", "Open Elective II", 3),
            ("CE3203L", "Environmental Engineering Lab", 1.5),
            ("CE3201L", "Computer Aided Building Design & Drafting Lab", 1.5),
        ],
        7: [
            ("CE4101", "Estimation, Costing, Specifications & Valuation", 3),
            ("CE4102", "Professional Elective III (Prestressed Concrete / Ground Improvement Techniques)", 3),
            ("CE4103", "Professional Elective IV (Earthquake Resistant Engineering / Construction Management)", 3),
            ("CE4104", "Professional Elective V (Urban Hydrology / Air Pollution & Control)", 3),
            ("OE4101", "Open Elective III", 3),
            ("CE4105P", "Industrial Training & Structural Mini Project", 3),
        ],
        8: [
            ("CE4201P", "Major Project Work Phase-II (Civil Infrastructure Capstone)", 8),
            ("CE4202S", "Comprehensive Viva-Voce & Field Study Defense", 4),
        ]
    }
}

RESUME_REQUIREMENTS = [
    {
        "name": "Personal Information",
        "type": "text",
        "value": "Full name, mobile number, email address, location.",
        "order": 1
    },
    {
        "name": "Career Objective",
        "type": "text",
        "value": "Short statement about career goals and professional interests.",
        "order": 2
    },
    {
        "name": "Educational Qualifications",
        "type": "heading",
        "value": "College name, degree, branch, graduation year, CGPA/percentage.",
        "order": 3
    },
    {
        "name": "Technical Skills",
        "type": "text",
        "value": "Programming languages, technologies, tools, and software skills.",
        "order": 4
    },
    {
        "name": "Projects",
        "type": "heading",
        "value": "Project title, description, technologies used, and key features.",
        "order": 5
    },
    {
        "name": "Certifications",
        "type": "text",
        "value": "Certification name, issuing organization, and completion date.",
        "order": 6
    },
    {
        "name": "Internship / Work Experience",
        "type": "heading",
        "value": "Organization, role, duration, and responsibilities.",
        "order": 7
    },
    {
        "name": "Achievements",
        "type": "text",
        "value": "Awards, hackathons, competitions, and academic achievements.",
        "order": 8
    },
    {
        "name": "Strengths",
        "type": "text",
        "value": "Problem-solving, teamwork, communication, adaptability, and quick learning.",
        "order": 9
    },
    {
        "name": "Additional Information",
        "type": "text",
        "value": "Languages known, extracurricular activities, and relevant interests.",
        "order": 10
    }
]

def seed_academic_system():
    with get_db_cursor(commit=True) as cursor:
        print("1. Ensuring Institution exists...")
        cursor.execute("SELECT id FROM institution WHERE id = %s", (INSTITUTION_ID,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO institution (id, name, code, email, is_active)
                VALUES (%s, 'Anantha Lakshmi Institute of Technology and Sciences', 'ALITS', 'compliance@alits.ac.in', TRUE)
            """, (INSTITUTION_ID,))

        print("2. Ensuring all 9 Engineering Departments exist with full accredited names...")
        dept_ids = {}
        for d in DEPARTMENTS:
            cursor.execute("SELECT id FROM departments WHERE institution_id = %s AND UPPER(code) = UPPER(%s)", (INSTITUTION_ID, d["code"]))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE departments SET name = %s WHERE id = %s", (d["name"], row["id"]))
                dept_ids[d["code"]] = row["id"]
            else:
                cursor.execute("INSERT INTO departments (institution_id, code, name) VALUES (%s, %s, %s) RETURNING id", (INSTITUTION_ID, d["code"], d["name"]))
                dept_ids[d["code"]] = cursor.fetchone()["id"]

        print("Departments mapped:", dept_ids)

        print("3. Ensuring Academic Years and Semesters exist...")
        cursor.execute("SELECT id FROM academic_years WHERE institution_id = %s AND year_name = '2025-2026'", (INSTITUTION_ID,))
        curr_ay = cursor.fetchone()
        ay_id = curr_ay["id"] if curr_ay else 3

        sem_map = {}
        for sem_num in range(1, 9):
            yr = ((sem_num - 1) // 2) + 1
            sem_in_yr = ((sem_num - 1) % 2) + 1
            code = f"SEM {yr}-{sem_in_yr}"
            cursor.execute("""
                SELECT id FROM semesters WHERE institution_id = %s AND semester_number = %s
            """, (INSTITUTION_ID, sem_num))
            s_row = cursor.fetchone()
            if s_row:
                sem_map[sem_num] = s_row["id"]
            else:
                cursor.execute("""
                    INSERT INTO semesters (institution_id, semester_name, semester_code, semester_number)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, (INSTITUTION_ID, f"Year {yr} - Semester {sem_in_yr}", code, sem_num))
                sem_map[sem_num] = cursor.fetchone()["id"]

        print("Semesters mapped (1-8):", sem_map)

        print("4. Ensuring Exam Categories exist...")
        exam_cats = [
            ("MID1", "Mid Examination - I", 40, 1),
            ("MID2", "Mid Examination - II", 40, 2),
            ("SEM", "Semester End Examination", 70, 3),
        ]
        for c_code, c_name, marks, order in exam_cats:
            cursor.execute("SELECT id FROM exam_categories WHERE institution_id = %s AND code = %s", (INSTITUTION_ID, c_code))
            erow = cursor.fetchone()
            if erow:
                cursor.execute("UPDATE exam_categories SET name = %s, max_marks = %s, display_order = %s WHERE id = %s", (c_name, marks, order, erow["id"]))
            else:
                cursor.execute("INSERT INTO exam_categories (institution_id, code, name, max_marks, is_mandatory, display_order) VALUES (%s, %s, %s, %s, TRUE, %s)", (INSTITUTION_ID, c_code, c_name, marks, order))

        print("5. Seeding all HOD and Faculty accounts for each branch...")
        hod_hash = hash_password("HOD@123")
        faculty_hash = hash_password("Faculty@123")
        admin_hash = hash_password("Admin@123")
        auditor_hash = hash_password("Auditor@123")

        def upsert_user(dept_id, name, email, password_hash, role):
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE users 
                    SET institution_id = %s, department_id = %s, name = %s, password_hash = %s, role = %s, is_active = TRUE 
                    WHERE id = %s
                """, (INSTITUTION_ID, dept_id, name, password_hash, role, existing["id"]))
                return existing["id"]
            else:
                cursor.execute("""
                    INSERT INTO users (institution_id, department_id, name, email, password_hash, role, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE) RETURNING id
                """, (INSTITUTION_ID, dept_id, name, email, password_hash, role))
                return cursor.fetchone()["id"]

        # Admin & Auditor
        upsert_user(None, "Admin", "admin@alits.ac.in", admin_hash, "Admin")
        upsert_user(None, "Auditor", "auditor@alits.ac.in", auditor_hash, "Auditor")

        # Branch HODs & Faculty
        hod_emails = {
            "CSE": "hod.cse@alits.ac.in",
            "CSD": "hod.csd@alits.ac.in",
            "CSM": "hod.csm@alits.ac.in",
            "CSE-AIML": "hod.aiml@alits.ac.in",
            "CAI": "hod.cai@alits.ac.in",
            "ECE": "hod.ece@alits.ac.in",
            "EEE": "hod.eee@alits.ac.in",
            "ME": "hod.me@alits.ac.in",
            "CE": "hod.ce@alits.ac.in",
        }
        faculty_emails = {
            "CSE": "faculty.cse@alits.ac.in",
            "CSD": "faculty.csd@alits.ac.in",
            "CSM": "faculty.csm@alits.ac.in",
            "CSE-AIML": "faculty.aiml@alits.ac.in",
            "CAI": "faculty.cai@alits.ac.in",
            "ECE": "faculty.ece@alits.ac.in",
            "EEE": "faculty.eee@alits.ac.in",
            "ME": "faculty.me@alits.ac.in",
            "CE": "faculty.ce@alits.ac.in",
        }

        hod_user_ids = {}
        faculty_user_ids = {}

        for code, d_id in dept_ids.items():
            h_email = hod_emails.get(code, f"hod.{code.lower()}@alits.ac.in")
            hod_user_ids[code] = upsert_user(d_id, "HOD", h_email, hod_hash, "HOD")

            f_email = faculty_emails.get(code, f"faculty.{code.lower()}@alits.ac.in")
            faculty_user_ids[code] = upsert_user(d_id, "Faculty", f_email, faculty_hash, "Faculty")

        # Prototype accounts with same passwords
        upsert_user(None, "Admin", "admin.alits@alitsprototype.test", admin_hash, "Admin")
        upsert_user(None, "Auditor", "auditor.alits@alitsprototype.test", auditor_hash, "Auditor")
        upsert_user(dept_ids["CSE"], "HOD", "hod.cse@alitsprototype.test", hod_hash, "HOD")
        upsert_user(dept_ids["CSE"], "Faculty", "faculty.cse@alitsprototype.test", faculty_hash, "Faculty")

        for special_email in ["faculty@alits.ac.in", "testloginuser@example.com", "odigepallisnehareddy@gmail.com"]:
            upsert_user(dept_ids["CSE"], "Faculty", special_email, faculty_hash, "Faculty")

        print(f"HODs created: {len(hod_user_ids)}, Faculty created: {len(faculty_user_ids)}")

        print("6. Seeding JNTU Curriculum for all branches (1-1 to 4-2)...")
        total_courses_seeded = 0

        def upsert_course(dept_code, sem_num, c_code, c_name, credits):
            nonlocal total_courses_seeded
            d_id = dept_ids[dept_code]
            s_id = sem_map[sem_num]
            f_id = faculty_user_ids.get(dept_code) or faculty_user_ids["CSE"]

            cursor.execute("""
                SELECT id FROM courses 
                WHERE institution_id = %s AND department_id = %s AND semester_id = %s AND course_code = %s
            """, (INSTITUTION_ID, d_id, s_id, c_code))
            existing = cursor.fetchone()

            if existing:
                course_id = existing["id"]
                cursor.execute("""
                    UPDATE courses SET course_name = %s, credits = %s, academic_year_id = %s WHERE id = %s
                """, (c_name, credits, ay_id, course_id))
            else:
                cursor.execute("""
                    INSERT INTO courses (institution_id, department_id, semester_id, academic_year_id, course_code, course_name, credits, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id
                """, (INSTITUTION_ID, d_id, s_id, ay_id, c_code, c_name, credits))
                course_id = cursor.fetchone()["id"]

            cursor.execute("""
                SELECT id FROM faculty_course_assignments 
                WHERE course_id = %s AND faculty_id = %s AND academic_year_id = %s
            """, (course_id, f_id, ay_id))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO faculty_course_assignments (course_id, faculty_id, academic_year_id)
                    VALUES (%s, %s, %s)
                """, (course_id, f_id, ay_id))

            total_courses_seeded += 1

        # Seed 1-1 and 1-2 for all branches (Common foundational curriculum)
        for dept_code in DEPARTMENTS:
            code = dept_code["code"]
            prefix = code.replace("-", "")[:2]
            for idx, (sub_code, sub_name, creds) in enumerate(COMMON_1_1, start=1):
                c_code = f"{prefix}110{idx}" if not sub_code.endswith("L") else f"{prefix}110{idx}L"
                upsert_course(code, 1, c_code, sub_name, creds)
            for idx, (sub_code, sub_name, creds) in enumerate(COMMON_1_2, start=1):
                c_code = f"{prefix}120{idx}" if not sub_code.endswith("L") else f"{prefix}120{idx}L"
                upsert_course(code, 2, c_code, sub_name, creds)

        # Seed 2-1 to 4-2 core subjects for all branches
        for b_code, sems in BRANCH_CURRICULUM.items():
            for s_num, subjects in sems.items():
                for c_code, c_name, creds in subjects:
                    upsert_course(b_code, s_num, c_code, c_name, creds)

        print(f"Total courses seeded/updated across all branches and semesters: {total_courses_seeded}")

        print("7. Ensuring 'Resume' document type and standard requirements exist...")
        cursor.execute("SELECT id FROM document_types WHERE name = 'Resume'")
        res_row = cursor.fetchone()
        if not res_row:
            cursor.execute("""
                INSERT INTO document_types (name, description, category, is_active)
                VALUES ('Resume', 'Faculty and Student Curriculum Vitae (10 Institutional Standards)', 'Portfolio', TRUE)
                RETURNING id
            """)
            resume_type_id = cursor.fetchone()["id"]
        else:
            resume_type_id = res_row["id"]
            cursor.execute("UPDATE document_types SET is_active = TRUE WHERE id = %s", (resume_type_id,))

        cursor.execute("""
            SELECT id FROM document_formats 
            WHERE institution_id = %s AND document_type_id = %s
        """, (INSTITUTION_ID, resume_type_id))
        fmt_row = cursor.fetchone()
        if not fmt_row:
            admin_id = upsert_user(None, "Admin", "admin@alits.ac.in", admin_hash, "Admin")
            cursor.execute("""
                INSERT INTO document_formats (institution_id, document_type_id, format_name, instructions, created_by)
                VALUES (%s, %s, 'Standard Institutional Resume / Curriculum Vitae Format', 'Comprehensive 10-point standard requirements for institutional resume verification.', %s)
                RETURNING id
            """, (INSTITUTION_ID, resume_type_id, admin_id))
            fmt_id = cursor.fetchone()["id"]
        else:
            fmt_id = fmt_row["id"]

        cursor.execute("DELETE FROM format_requirements WHERE format_id = %s", (fmt_id,))
        for req in RESUME_REQUIREMENTS:
            cursor.execute("""
                INSERT INTO format_requirements (format_id, requirement_name, requirement_type, requirement_value, is_required, display_order)
                VALUES (%s, %s, %s, %s, TRUE, %s)
            """, (fmt_id, req["name"], req["type"], req["value"], req["order"]))

        print("Resume document type and 10 standard requirements seeded successfully!")

if __name__ == "__main__":
    seed_academic_system()
    print("ALL BRANCHES, HODS, JNTU CURRICULA, AND RESUME FORMAT SEEDED SUCCESSFULLY!")
