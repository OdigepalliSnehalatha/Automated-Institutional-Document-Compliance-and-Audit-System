import { useEffect, useState } from "react";
import api from "./api";

function Format({ onBack }) {
  const [documentTypes, setDocumentTypes] = useState([]);
  const [selectedType, setSelectedType] = useState("");
  const [examType, setExamType] = useState("");

  const [formatName, setFormatName] = useState("");
  const [instructions, setInstructions] = useState("");

  const [requirements, setRequirements] = useState([
    {
      requirement_name: "",
      requirement_type: "required",
      requirement_value: "",
      is_required: true,
      display_order: 1,
    },
  ]);

  const [message, setMessage] = useState("");

  useEffect(() => {
    loadDocumentTypes();
  }, []);

  const loadDocumentTypes = async () => {
    try {
      const response = await api.get("/document-types");

      const allowedTypes = response.data.filter(
        (type) =>
          type.is_active === true &&
          (
            type.name === "Course Structure" ||
            type.name === "Question Bank" ||
            type.name === "Question Paper"
          )
      );

      setDocumentTypes(allowedTypes);
    } catch (error) {
      console.error(error);
      setMessage("Failed to load document types.");
    }
  };

  const selectedDocumentType = documentTypes.find(
    (type) => String(type.id) === String(selectedType)
  );

  const handleDocumentTypeChange = (value) => {
    setSelectedType(value);

    const selected = documentTypes.find(
      (type) => String(type.id) === String(value)
    );

    if (selected?.name !== "Question Paper") {
      setExamType("");
    }

    setRequirements([
      {
        requirement_name: "",
        requirement_type: "required",
        requirement_value: "",
        is_required: true,
        display_order: 1,
      },
    ]);

    setMessage("");
  };

  const addRequirement = () => {
    setRequirements([
      ...requirements,
      {
        requirement_name: "",
        requirement_type: "required",
        requirement_value: "",
        is_required: true,
        display_order: requirements.length + 1,
      },
    ]);
  };

  const updateRequirement = (index, field, value) => {
    const updated = [...requirements];

    updated[index] = {
      ...updated[index],
      [field]: value,
    };

    setRequirements(updated);
  };

  const removeRequirement = (index) => {
    const updated = requirements.filter(
      (_, i) => i !== index
    );

    setRequirements(
      updated.map((item, index) => ({
        ...item,
        display_order: index + 1,
      }))
    );
  };

  const addCourseStructureRequirements = () => {
    const courseStructureRequirements = [
      {
        requirement_name: "College Name",
        requirement_type: "text",
        requirement_value:
          "College name must be present",
        is_required: true,
      },
      {
        requirement_name: "Course Name",
        requirement_type: "text",
        requirement_value:
          "Course name must be present",
        is_required: true,
      },
      {
        requirement_name: "Course Code",
        requirement_type: "text",
        requirement_value:
          "Course code must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 1 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 1 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 1 Topics",
        requirement_type: "text",
        requirement_value:
          "Unit 1 topics section must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 2 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 2 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 2 Topics",
        requirement_type: "text",
        requirement_value:
          "Unit 2 topics section must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 3 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 3 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 3 Topics",
        requirement_type: "text",
        requirement_value:
          "Unit 3 topics section must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 4 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 4 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 4 Topics",
        requirement_type: "text",
        requirement_value:
          "Unit 4 topics section must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 5 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 5 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 5 Topics",
        requirement_type: "text",
        requirement_value:
          "Unit 5 topics section must be present",
        is_required: true,
      },
    ];

    setRequirements(
      courseStructureRequirements.map(
        (item, index) => ({
          ...item,
          display_order: index + 1,
        })
      )
    );
  };

  const addQuestionBankRequirements = () => {
    const questionBankRequirements = [
      {
        requirement_name: "College Name",
        requirement_type: "text",
        requirement_value:
          "College name must be present",
        is_required: true,
      },
      {
        requirement_name: "Course Name",
        requirement_type: "text",
        requirement_value:
          "Course name must be present",
        is_required: true,
      },
      {
        requirement_name: "Course Code",
        requirement_type: "text",
        requirement_value:
          "Course code must be present",
        is_required: true,
      },
      {
        requirement_name: "Semester",
        requirement_type: "text",
        requirement_value:
          "Semester information must be present",
        is_required: true,
      },

      {
        requirement_name: "Unit 1 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 1 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 1 Part A",
        requirement_type: "required",
        requirement_value:
          "Unit 1 Part A must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 1 Part A Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 1 Part A Marks Per Question",
        requirement_type: "marks",
        requirement_value: "2",
        is_required: true,
      },
      {
        requirement_name: "Unit 1 Part B",
        requirement_type: "required",
        requirement_value:
          "Unit 1 Part B must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 1 Part B Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 1 Part B Marks Per Question",
        requirement_type: "marks",
        requirement_value: "10",
        is_required: true,
      },

      {
        requirement_name: "Unit 2 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 2 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 2 Part A",
        requirement_type: "required",
        requirement_value:
          "Unit 2 Part A must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 2 Part A Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 2 Part A Marks Per Question",
        requirement_type: "marks",
        requirement_value: "2",
        is_required: true,
      },
      {
        requirement_name: "Unit 2 Part B",
        requirement_type: "required",
        requirement_value:
          "Unit 2 Part B must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 2 Part B Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 2 Part B Marks Per Question",
        requirement_type: "marks",
        requirement_value: "10",
        is_required: true,
      },

      {
        requirement_name: "Unit 3 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 3 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 3 Part A",
        requirement_type: "required",
        requirement_value:
          "Unit 3 Part A must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 3 Part A Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 3 Part A Marks Per Question",
        requirement_type: "marks",
        requirement_value: "2",
        is_required: true,
      },
      {
        requirement_name: "Unit 3 Part B",
        requirement_type: "required",
        requirement_value:
          "Unit 3 Part B must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 3 Part B Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 3 Part B Marks Per Question",
        requirement_type: "marks",
        requirement_value: "10",
        is_required: true,
      },

      {
        requirement_name: "Unit 4 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 4 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 4 Part A",
        requirement_type: "required",
        requirement_value:
          "Unit 4 Part A must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 4 Part A Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 4 Part A Marks Per Question",
        requirement_type: "marks",
        requirement_value: "2",
        is_required: true,
      },
      {
        requirement_name: "Unit 4 Part B",
        requirement_type: "required",
        requirement_value:
          "Unit 4 Part B must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 4 Part B Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 4 Part B Marks Per Question",
        requirement_type: "marks",
        requirement_value: "10",
        is_required: true,
      },

      {
        requirement_name: "Unit 5 Heading",
        requirement_type: "text",
        requirement_value:
          "Unit 5 heading must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 5 Part A",
        requirement_type: "required",
        requirement_value:
          "Unit 5 Part A must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 5 Part A Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 5 Part A Marks Per Question",
        requirement_type: "marks",
        requirement_value: "2",
        is_required: true,
      },
      {
        requirement_name: "Unit 5 Part B",
        requirement_type: "required",
        requirement_value:
          "Unit 5 Part B must be present",
        is_required: true,
      },
      {
        requirement_name: "Unit 5 Part B Questions",
        requirement_type: "question_count",
        requirement_value: "10",
        is_required: true,
      },
      {
        requirement_name: "Unit 5 Part B Marks Per Question",
        requirement_type: "marks",
        requirement_value: "10",
        is_required: true,
      },
    ];

    setRequirements(
      questionBankRequirements.map(
        (item, index) => ({
          ...item,
          display_order: index + 1,
        })
      )
    );
  };

  const addQuestionPaperRequirements = () => {
    const questionPaperRequirements = [
      {
        requirement_name: "College Header",
        requirement_type: "required",
        requirement_value:
          "College header must be present",
        is_required: true,
      },
      {
        requirement_name: "Semester",
        requirement_type: "text",
        requirement_value:
          "Semester information must be present",
        is_required: true,
      },
      {
        requirement_name: "B.Tech",
        requirement_type: "text",
        requirement_value:
          "B.Tech programme information must be present",
        is_required: true,
      },
      {
        requirement_name: "Examination Type",
        requirement_type: "text",
        requirement_value:
          examType,
        is_required: true,
      },
      {
        requirement_name: "Subject Name",
        requirement_type: "text",
        requirement_value:
          "Subject name must be present",
        is_required: true,
      },
      {
        requirement_name: "Subject Code",
        requirement_type: "text",
        requirement_value:
          "Subject code must be present",
        is_required: true,
      },
      {
        requirement_name: "Branch",
        requirement_type: "text",
        requirement_value:
          "Branch must be present",
        is_required: true,
      },
      {
        requirement_name: "Department",
        requirement_type: "text",
        requirement_value:
          "Department must be present",
        is_required: true,
      },
      {
        requirement_name: "Time",
        requirement_type: "text",
        requirement_value:
          "Time must be present",
        is_required: true,
      },
      {
        requirement_name: "Maximum Marks",
        requirement_type: "text",
        requirement_value:
          "Maximum marks must be present",
        is_required: true,
      },
      {
        requirement_name: "Part A",
        requirement_type: "required",
        requirement_value:
          "Part A must be present",
        is_required: true,
      },
      {
        requirement_name: "Part A Questions",
        requirement_type: "question_count",
        requirement_value:
          examType === "Mid Examination"
            ? "5"
            : "10",
        is_required: true,
      },
      {
        requirement_name: "Part A Marks",
        requirement_type: "marks",
        requirement_value:
          "2 marks per question",
        is_required: true,
      },
      {
        requirement_name: "Part A Arrangement",
        requirement_type: "arrangement",
        requirement_value:
          "Part A must follow the predefined arrangement",
        is_required: true,
      },
      {
        requirement_name: "Part B",
        requirement_type: "required",
        requirement_value:
          "Part B must be present",
        is_required: true,
      },
      {
        requirement_name: "Part B Questions",
        requirement_type: "question_count",
        requirement_value:
          examType === "Mid Examination"
            ? "6"
            : "10",
        is_required: true,
      },
      {
        requirement_name: "Part B Marks",
        requirement_type: "marks",
        requirement_value:
          "10 marks per question",
        is_required: true,
      },
      {
        requirement_name: "Part B Arrangement",
        requirement_type: "arrangement",
        requirement_value:
          "Part B must follow the predefined arrangement",
        is_required: true,
      },
      {
        requirement_name: "Body",
        requirement_type: "required",
        requirement_value:
          "Question paper body must be present",
        is_required: true,
      },
      {
        requirement_name: "Footer",
        requirement_type: "required",
        requirement_value:
          "Footer must be present",
        is_required: true,
      },
    ];

    setRequirements(
      questionPaperRequirements.map(
        (item, index) => ({
          ...item,
          display_order: index + 1,
        })
      )
    );
  };

  const loadStandardRequirements = () => {
    if (selectedDocumentType?.name === "Course Structure") {
      addCourseStructureRequirements();
    } else if (
      selectedDocumentType?.name === "Question Bank"
    ) {
      addQuestionBankRequirements();
    } else if (
      selectedDocumentType?.name === "Question Paper"
    ) {
      if (!examType) {
        setMessage(
          "Please select Mid Examination or Semester Examination."
        );
        return;
      }

      addQuestionPaperRequirements();
    }
  };

  const saveFormat = async () => {
    try {
      setMessage("");

      if (!selectedType) {
        setMessage(
          "Please select a document type."
        );
        return;
      }

      if (
        selectedDocumentType?.name ===
          "Question Paper" &&
        !examType
      ) {
        setMessage(
          "Please select Mid Examination or Semester Examination."
        );
        return;
      }

      if (!formatName.trim()) {
        setMessage(
          "Please enter a format name."
        );
        return;
      }

      if (requirements.length === 0) {
        setMessage(
          "Please add at least one structural requirement."
        );
        return;
      }

      const finalInstructions =
        selectedDocumentType?.name ===
        "Question Paper"
          ? `${examType}. ${instructions.trim()}`
          : instructions.trim();

      const formatResponse = await api.post(
        "/formats",
        {
          institution_id: 1,
          department_id: 1,
          document_type_id:
            Number(selectedType),
          format_name:
            formatName.trim(),
          instructions:
            finalInstructions,
        }
      );

      const formatId =
        formatResponse.data.format.id;

      for (const requirement of requirements) {
        if (
          !requirement.requirement_name.trim()
        ) {
          continue;
        }

        await api.post(
          "/format-requirements",
          {
            format_id: formatId,
            requirement_name:
              requirement.requirement_name.trim(),
            requirement_type:
              requirement.requirement_type,
            requirement_value:
              requirement.requirement_value.trim(),
            is_required:
              requirement.is_required,
            display_order:
              requirement.display_order,
          }
        );
      }

      setMessage(
        "Format saved successfully."
      );

    } catch (error) {
      console.error(error);

      setMessage(
        error.response?.data?.detail ||
        "Failed to save format."
      );
    }
  };

  return (
    <div
      style={{
        padding: "30px",
      }}
    >
      <button onClick={onBack}>
        ← Back
      </button>

      <h1>
        Format Management
      </h1>

      <p>
        Define the structural requirements
        that will be used to evaluate
        uploaded documents.
      </p>

      <hr />

      <h2>
        Document Type
      </h2>

      <select
        value={selectedType}
        onChange={(e) =>
          handleDocumentTypeChange(
            e.target.value
          )
        }
      >
        <option value="">
          Select Document Type
        </option>

        {documentTypes.map((type) => (
          <option
            key={type.id}
            value={type.id}
          >
            {type.name}
          </option>
        ))}
      </select>

      {selectedDocumentType?.name ===
        "Question Paper" && (
        <>
          <h2>
            Examination Type
          </h2>

          <select
            value={examType}
            onChange={(e) =>
              setExamType(
                e.target.value
              )
            }
          >
            <option value="">
              Select Examination Type
            </option>

            <option value="Mid Examination">
              Mid Examination
            </option>

            <option value="Semester Examination">
              Semester Examination
            </option>
          </select>
        </>
      )}

      {selectedDocumentType && (
        <div
          style={{
            marginTop: "15px",
            marginBottom: "15px",
          }}
        >
          <button
            onClick={
              loadStandardRequirements
            }
          >
            Load Standard Requirements
          </button>
        </div>
      )}

      <h2>
        Format Name
      </h2>

      <input
        type="text"
        value={formatName}
        onChange={(e) =>
          setFormatName(
            e.target.value
          )
        }
        placeholder={
          selectedDocumentType?.name ===
          "Question Paper"
            ? "Example: CSE Mid Examination Format"
            : "Example: CSE Document Format"
        }
        style={{
          width: "500px",
          padding: "8px",
        }}
      />

      <h2>
        General Instructions
      </h2>

      <textarea
        value={instructions}
        onChange={(e) =>
          setInstructions(
            e.target.value
          )
        }
        placeholder={
          selectedDocumentType?.name ===
          "Question Paper"
            ? "Example: Compare only structural format. Do not compare question meaning or numbering."
            : "Enter instructions for evaluating this document..."
        }
        rows="6"
        style={{
          width: "600px",
          padding: "8px",
        }}
      />

      <h2>
        Structural Requirements
      </h2>

      {requirements.map(
        (requirement, index) => (
          <div
            key={index}
            style={{
              border:
                "1px solid #ccc",
              padding: "15px",
              marginBottom:
                "15px",
            }}
          >
            <h3>
              Requirement{" "}
              {index + 1}
            </h3>

            <input
              type="text"
              placeholder="Requirement name"
              value={
                requirement.requirement_name
              }
              onChange={(e) =>
                updateRequirement(
                  index,
                  "requirement_name",
                  e.target.value
                )
              }
              style={{
                width: "300px",
                padding: "8px",
              }}
            />

            <br />
            <br />

            <label>
              Requirement Type
            </label>

            <br />

            <select
              value={
                requirement.requirement_type
              }
              onChange={(e) =>
                updateRequirement(
                  index,
                  "requirement_type",
                  e.target.value
                )
              }
            >
              <option value="required">
                Required Element
              </option>

              <option value="text">
                Text / Section
              </option>

              <option value="question_count">
                Question Count
              </option>

              <option value="marks">
                Marks
              </option>

              <option value="arrangement">
                Arrangement
              </option>

              <option value="logo">
                Logo
              </option>
            </select>

            <br />
            <br />

            <textarea
              placeholder="Enter requirement details..."
              value={
                requirement.requirement_value
              }
              onChange={(e) =>
                updateRequirement(
                  index,
                  "requirement_value",
                  e.target.value
                )
              }
              rows="4"
              style={{
                width: "500px",
                padding: "8px",
              }}
            />

            <br />
            <br />

            <label>
              <input
                type="checkbox"
                checked={
                  requirement.is_required
                }
                onChange={(e) =>
                  updateRequirement(
                    index,
                    "is_required",
                    e.target.checked
                  )
                }
              />

              {" "}
              Required
            </label>

            <br />
            <br />

            <button
              onClick={() =>
                removeRequirement(
                  index
                )
              }
            >
              Remove
            </button>
          </div>
        )
      )}

      <button
        onClick={addRequirement}
      >
        + Add Requirement
      </button>

      <br />
      <br />

      <button
        onClick={saveFormat}
      >
        Save Format
      </button>

      {message && (
        <p
          style={{
            marginTop: "20px",
            fontWeight: "bold",
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
}

export default Format;