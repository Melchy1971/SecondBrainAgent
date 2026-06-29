---
title: "n8n Workflow Übersetzung"
type: chatgpt_conversation
source: chatgpt
source_id: "683ea4cf-b674-8007-b6e7-897818b11341"
created: 2025-06-03
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# n8n Workflow Übersetzung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `683ea4cf-b674-8007-b6e7-897818b11341`
- Nachrichten: 10

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

übersetze  mir nach deutsch. {
  "id": "CDVBZRDH5gNUzIml",
  "meta": {
    "instanceId": "ab60b809a7fa5daa22fa7edffc14e989a6e59d4063ec838ad62f2655caafd963",
    "templateCredsSetupCompleted": true
  },
  "name": "N8N for Beginners: Looping over Items",
  "tags": [],
  "nodes": [
    {
      "id": "500304a1-5164-4907-b0a7-e514e455e3dc",
      "name": "Result1",
      "type": "n8n-nodes-base.noOp",
      "notes": "Look Here to see resulting output",
      "position": [
        880,
        -280
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },
    {
      "id": "32808ad1-1a35-497f-b1d3-c935a924c541",
      "name": "Result2",
      "type": "n8n-nodes-base.noOp",
      "notes": "Look here to see resulting output",
      "position": [
        880,
        40
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },
    {
      "id": "f3c9fa5d-a4c7-4cf0-beb5-774d8483974f",
      "name": "Sticky Note",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        -340
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 240,
        "content": "\n### Result1 shows that the array of strings is seen as one item by Loop1"
      },
      "typeVersion": 1
    },
    {
      "id": "0bb96765-60ce-4618-9b39-7cd203a3cb48",
      "name": "Sticky Note1",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        -60
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 260,
        "content": "### Result2 shows that the Loop2 sees 5 items after the array of strings is split into separate objects"
      },
      "typeVersion": 1
    },
    {
      "id": "b71fcc86-b0cd-4241-b0d6-21abe4c6b68d",
      "name": "Sticky Note2",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        -1680,
        -1100
      ],
      "parameters": {
        "width": 1200,
        "height": 2480,
        "content": "# N8N for Beginners: Looping Over Items\n\n## Description\n\nThis workflow is designed for **n8n beginners** to understand how n8n handles **looping (iteration)** over multiple items. It highlights two key behaviors:\n\n- **Built-In Looping:** By default, most n8n nodes iterate over each item in an input array.\n- **Explicit Looping:** The **Loop Over Items** node allows controlled iteration, enabling **custom batch processing** and multi-step workflows.\n\nThis workflow demonstrates the difference between processing an **unsplit array of strings (single item)** vs. **a split array (multiple items)**.\n\n---\n\n## Setup\n\n### 1. Input Data\n\nTo begin, **paste the following JSON** into the **Manual Trigger** node:\n\n```json\n{\n  \"urls\": [\n    \"https://www.reddit.com\",\n    \"https://www.n8n.io/\",\n    \"https://n8n.io/\",\n    \"https://supabase.com/\",\n    \"https://duckduckgo.com/\"\n  ]\n}\n```\n\nðŸ“Œ **Steps to Paste Data:**\n- **Double-click** the \"Manual Trigger\" node.\n- Click **\"Edit Output\"** (top-right corner).\n- Paste the JSON and **Save**.\n- The node **turns purple**, indicating that test data is pinned. \n\n---\n\n## Explanation of the n8n Nodes in the Workflow\n\n### Manual Trigger  \nThis node starts the workflow manually and sends test data.  \n**Documentation:** [Manual Trigger Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.manualtrigger/)\n\n### Split Out (Split Array of Strings into Array of Objects)  \nExtracts the `urls` array and splits it so that each URL becomes a separate JSON object.  \n**Documentation:** [Split Out Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitout/)\n\n### Loop Over Items (Loop Over Items 1)  \nDemonstrates how an **unsplit** array is treated as one item, processing it as a single unit.  \n**Documentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)\n\n### Loop Over Items (Loop Over Items 2)  \nProcesses the **split array** one item at a time. This demonstrates individual iteration and controlled looping.  \n**Documentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)\n\n### Wait Node  \nIntroduces a **1-second delay** per iteration to demonstrate sequential execution. This can be removed for faster performance.  \n**Documentation:** [Wait Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/)\n\n### Code Nodes (Add param1 to outputX)  \nEach Code node adds a constant field (`param1`) to the data, ensuring that every item gets enriched with the same parameter.  \n**Documentation:** [Code Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/)\n\n### NoOp Nodes (Result1, Result2, Result3, Result4, Result5)\nThese nodes display the output at different stages of the workflow for inspection.\n**Documentation:** [NoOp Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.noop/)\n\n\n\n---\n\n## Execution Details\n\n### 1. How the Workflow Runs\n\n- **Manual Trigger starts execution** with the pasted JSON data.\n- The workflow follows **two paths**:\n\n#### Unsplit Array Path â†’ Loop Over Items 1  \n- The original JSON is processed **as a single item**.  \n- **Result1 & Result5:** Show that the array was **not split** before processing.\n\n#### Split Array Path â†’ Split Out â†’ Loop Over Items 2  \n- The **Split Out** node converts the `urls` array into separate objects.\n- The **Loop Over Items 2** node processes each URL **one by one**.\n- A **Wait node** (1-second delay) demonstrates **controlled execution**.\n- **Code nodes** modify the JSON, adding the field (`param1`).\n- **Result2, Result3, Result4:** Display the final processed output.\n\n### 2. What You Will See\n\n- **Result1 & Result5:** The entire array is processed **as one item** before splitting.\n- **Result2, Result3, Result4:** Each URL is processed **individually** after being split.\n- **Wait Node:** Adds a **1-second delay per item** in **Loop Over Items 2**.\n\n---\n\n## Notes\n\n- Sticky notes are included in the workflow **for easy reference**.\n- The **Wait node** is **optional**â€”remove it for faster execution.\n- This template is structured for **beginners** but serves as a **building block** for more advanced automations.\n\n---\n\n"
      },
      "typeVersion": 1
    },
    {
      "id": "53e7d23a-2a4f-4ada-aeb5-de128acf8625",
      "name": "Split Array of Strings into Array of Objects",
      "type": "n8n-nodes-base.splitOut",
      "position": [
        -20,
        380
      ],
      "parameters": {
        "options": {
          "destinationFieldName": "url"
        },
        "fieldToSplitOut": "urls"
      },
      "typeVersion": 1
    },
    {
      "id": "4910fec6-d600-43be-97b2-5050039db416",
      "name": "Sticky Note3",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        700
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 260,
        "content": "### Result4 shows that we can turn off the looping feature by setting the looping behavior to \"Run Once For All Items\""
      },
      "typeVersion": 1
    },
    {
      "id": "f0e68b30-5341-4672-8d8e-7a24d894eb03",
      "name": "Sticky Note4",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        420
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 240,
        "content": "### Result3 shows that looping over items is built in to n8n nodes"
      },
      "typeVersion": 1
    },
    {
      "id": "70a987b9-6a4a-49c3-a87c-0dd9cc1879ed",
      "name": "Result3",
      "type": "n8n-nodes-base.noOp",
      "notes": "Look here to see resulting output",
      "position": [
        900,
        500
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },
    {
      "id": "9de5fac9-e987-4fb1-8f7f-b59af2985e5c",
      "name": "Result4",
      "type": "n8n-nodes-base.noOp",
      "notes": "Look here to see resulting output",
      "position": [
        900,
        780
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },
    {
      "id": "d5fee847-7758-44ac-a270-6334dd81bb97",
      "name": "Sticky Note5",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        -640
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 260,
        "content": "### Result5 shows that the array of strings is seen as one item by Code5. So the behavior is the same as Loop1"
      },
      "typeVersion": 1
    },
    {
      "id": "9a134620-4067-4c7a-8b0f-30e19c93a66c",
      "name": "Result5",
      "type": "n8n-nodes-base.noOp",
      "notes": "Look here to see resulting output",
      "position": [
        880,
        -540
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },
    {
      "id": "c273cd55-708d-4f86-81f2-3bbe991f59f8",
      "name": "Paste JSON into this node",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [
        -400,
        -540
      ],
      "parameters": {},
      "typeVersion": 1
    },
    {
      "id": "8f64b987-05c5-43a9-89c0-201499df0aa6",
      "name": "Add param1 to output5",
      "type": "n8n-nodes-base.code",
      "position": [
        320,
        -540
      ],
      "parameters": {
        "jsCode": "\n  $json.param1 =  'add_me_to_all_items_and_name_me_param1';\n\n\nreturn $json"
      },
      "typeVersion": 2,
      "alwaysOutputData": true
    },
    {
      "id": "4920b4e4-b511-4059-b38a-623d14b6df25",
      "name": "Add param1 to output1",
      "type": "n8n-nodes-base.code",
      "position": [
        500,
        -180
      ],
      "parameters": {
        "mode": "runOnceForEachItem",
        "jsCode": "\n  $json.param1 = \"add_me_to_all_items_and_name_me_param1\"\n\nreturn $json"
      },
      "typeVersion": 2,
      "alwaysOutputData": true
    },
    {
      "id": "28ce5239-6437-4b7a-9395-3beb162fded6",
      "name": "Loop over Items 2",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [
        320,
        60
      ],
      "parameters": {
        "options": {}
      },
      "typeVersion": 3
    },
    {
      "id": "628edc5e-1b7f-4f50-9c29-8990bd4a5cc0",
      "name": "Loop over Items 1",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [
        320,
        -260
      ],
      "parameters": {
        "options": {
          "reset": false
        }
      },
      "typeVersion": 3
    },
    {
      "id": "ffccda97-066d-4c13-b4eb-a13ff849b90a",
      "name": "Add param1 to output2",
      "type": "n8n-nodes-base.code",
      "position": [
        680,
        220
      ],
      "parameters": {
        "mode": "runOnceForEachItem",
        "jsCode": "\n  $json.param1 =   \"add_me_to_all_items_and_name_me_param1\"\n\n\nreturn $json"
      },
      "typeVersion": 2,
      "alwaysOutputData": true
    },
    {
      "id": "6fb44840-6365-46db-9c50-eecd420f274f",
      "name": "Add param1 to output3",
      "type": "n8n-nodes-base.code",
      "position": [
        320,
        500
      ],
      "parameters": {
        "mode": "runOnceForEachItem",
        "jsCode": "\n  $json.param1 =   \"add_me_to_all_items_and_name_me_param1\"\n\n\nreturn $json"
      },
      "typeVersion": 2,
      "alwaysOutputData": true
    },
    {
      "id": "51b8d766-25ed-407f-a956-693b93bda95f",
      "name": "Add param1 to output4",
      "type": "n8n-nodes-base.code",
      "position": [
        320,
        780
      ],
      "parameters": {
        "jsCode": "\n  $json.param1 =   \"add_me_to_all_items_and_name_me_param1\"\n\n\nreturn $json"
      },
      "typeVersion": 2,
      "alwaysOutputData": true
    },
    {
      "id": "f8edde34-cf47-42e2-bbd3-552df2509451",
      "name": "Wait one second(just for show)",
      "type": "n8n-nodes-base.wait",
      "position": [
        480,
        180
      ],
      "webhookId": "61aef80b-4e9d-43ae-a083-cd87b4fdec11",
      "parameters": {
        "amount": 1
      },
      "typeVersion": 1.1
    }
  ],
  "active": false,
  "pinData": {},
  "settings": {
    "executionOrder": "v1"
  },
  "versionId": "e1eff37a-1ffd-4691-9560-eada5baab88d",
  "connections": {
    "Result1": {
      "main": [
        []
      ]
    },
    "Result2": {
      "main": [
        []
      ]
    },
    "Loop over Items 1": {
      "main": [
        [
          {
            "node": "Result1",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Add param1 to output1",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Loop over Items 2": {
      "main": [
        [
          {
            "node": "Result2",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Wait one second(just for show)",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Add param1 to output1": {
      "main": [
        [
          {
            "node": "Loop over Items 1",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Add param1 to output2": {
      "main": [
        [
          {
            "node": "Loop over Items 2",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Add param1 to output3": {
      "main": [
        [
          {
            "node": "Result3",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Add param1 to output4": {
      "main": [
        [
          {
            "node": "Result4",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Add param1 to output5": {
      "main": [
        [
          {
            "node": "Result5",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Paste JSON into this node": {
      "main": [
        [
          {
            "node": "Split Array of Strings into Array of Objects",
            "type": "main",
            "index": 0
          },
          {
            "node": "Add param1 to output5",
            "type": "main",
            "index": 0
          },
          {
            "node": "Loop over Items 1",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Wait one second(just for show)": {
      "main": [
        [
          {
            "node": "Add param1 to output2",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Split Array of Strings into Array of Objects": {
      "main": [
        [
          {
            "node": "Loop over Items 2",
            "type": "main",
            "index": 0
          },
          {
            "node": "Add param1 to output4",
            "type": "main",
            "index": 0
          },
          {
            "node": "Add param1 to output3",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}

### 2. Assistent

Hier ist dein Workflow in **deutscher Sprache**.  
Ich habe nur die für Menschen lesbaren Texte (Titel, Notes, Sticky-Notes-Inhalte u. Ä.) übersetzt – die technischen Knotennamen (“Result1” usw.) und alle Verbindungsbezüge wurden unverändert gelassen, damit der Workflow weiterhin korrekt importiert werden kann.

```json
{
  "id": "CDVBZRDH5gNUzIml",
  "meta": {
    "instanceId": "ab60b809a7fa5daa22fa7edffc14e989a6e59d4063ec838ad62f2655caafd963",
    "templateCredsSetupCompleted": true
  },
  "name": "n8n für Einsteiger: Schleifen über Elemente",
  "tags": [],
  "nodes": [
    {
      "id": "500304a1-5164-4907-b0a7-e514e455e3dc",
      "name": "Result1",
      "type": "n8n-nodes-base.noOp",
      "notes": "Hier klicken, um das Ergebnis zu sehen",
      "position": [
        880,
        -280
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },
    {
      "id": "32808ad1-1a35-497f-b1d3-c935a924c541",
      "name": "Result2",
      "type": "n8n-nodes-base.noOp",
      "notes": "Hier klicken, um das Ergebnis zu sehen",
      "position": [
        880,
        40
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },
    {
      "id": "f3c9fa5d-a4c7-4cf0-beb5-774d8483974f",
      "name": "Sticky Note",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        -340
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 240,
        "content": "\n### Result1 zeigt, dass das Array von Zeichenketten von Loop1 als ein einzelnes Element betrachtet wird"
      },
      "typeVersion": 1
    },
    {
      "id": "0bb96765-60ce-4618-9b39-7cd203a3cb48",
      "name": "Sticky Note1",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        -60
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 260,
        "content": "### Result2 zeigt, dass Loop2 fünf Elemente sieht, nachdem das String-Array in einzelne Objekte aufgeteilt wurde"
      },
      "typeVersion": 1
    },
    {
      "id": "b71fcc86-b0cd-4241-b0d6-21abe4c6b68d",
      "name": "Sticky Note2",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        -1680,
        -1100
      ],
      "parameters": {
        "width": 1200,
        "height": 2480,
        "content": "# n8n für Einsteiger: Schleifen über Elemente\n\n## Beschreibung\n\nDieser Workflow richtet sich an **n8n-Einsteiger**, um zu verstehen, wie n8n das **Schleifen (Iterieren)** über mehrere Items behandelt. Er hebt zwei wichtige Verhaltensweisen hervor:\n\n- **Eingebautes Schleifen:** Standardmäßig iterieren die meisten n8n-Knoten über jedes Element in einem Eingabe-Array.\n- **Explizites Schleifen:** Der **Loop Over Items**-Knoten ermöglicht eine gesteuerte Iteration, was **benutzerdefiniertes Batch-Processing** und mehrstufige Workflows erlaubt.\n\nDieser Workflow demonstriert den Unterschied zwischen der Verarbeitung eines **nicht aufgeteilten Arrays von Strings (ein einzelnes Item)** und eines **aufgeteilten Arrays (mehrere Items)**.\n\n---\n\n## Einrichtung\n\n### 1. Eingabedaten\n\nFüge zunächst **folgenden JSON-Code** in den **Manual Trigger**-Knoten ein:\n\n```json\n{\n  \"urls\": [\n    \"https://www.reddit.com\",\n    \"https://www.n8n.io/\",\n    \"https://n8n.io/\",\n    \"https://supabase.com/\",\n    \"https://duckduckgo.com/\"\n  ]\n}\n```\n\n📋 **So fügst du die Daten ein:**\n- **Doppelklicke** auf den „Manual Trigger“-Knoten.\n- Klicke oben rechts auf **„Edit Output“**.\n- Füge das JSON ein und **speichere**.\n- Der Knoten **färbt sich lila**, was zeigt, dass Testdaten angeheftet sind.\n\n---\n\n## Erläuterung der n8n-Knoten im Workflow\n\n### Manual Trigger  \nDieser Knoten startet den Workflow manuell und liefert Testdaten.  \n**Dokumentation:** [Manual Trigger Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.manualtrigger/)\n\n### Split Out (Array von Strings in Array von Objekten aufteilen)  \nExtrahiert das `urls`-Array und teilt es so auf, dass jede URL zu einem eigenen JSON-Objekt wird.  \n**Dokumentation:** [Split Out Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitout/)\n\n### Loop Over Items (Loop Over Items 1)  \nDemonstriert, wie ein **nicht aufgeteiltes** Array als ein einzelnes Item behandelt und als Einheit verarbeitet wird.  \n**Dokumentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)\n\n### Loop Over Items (Loop Over Items 2)  \nVerarbeitet das **aufgeteilte Array** Item für Item. Zeigt individuelle Iteration und kontrolliertes Schleifen.  \n**Dokumentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)\n\n### Wait Node  \nFügt eine **1-Sekunden-Verzögerung** pro Iteration hinzu, um sequentielle Ausführung zu zeigen. Kann für schnellere Abläufe entfernt werden.  \n**Dokumentation:** [Wait Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/)\n\n### Code-Knoten (Add param1 to outputX)  \nJeder Code-Knoten fügt das konstante Feld (`param1`) hinzu, sodass jedes Item um denselben Parameter erweitert wird.  \n**Dokumentation:** [Code Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/)\n\n### NoOp-Knoten (Result1, Result2, Result3, Result4, Result5)\nDiese Knoten zeigen die Ausgabe in verschiedenen Phasen des Workflows zur Kontrolle an.\n**Dokumentation:** [NoOp Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.noop/)\n\n---\n\n## Ausführungsdetails\n\n### 1. So läuft der Workflow\n\n- **Manual Trigger** startet die Ausführung mit den eingefügten JSON-Daten.\n- Der Workflow folgt **zwei Pfaden**:\n\n#### Pfad „Ungeteiltes Array“ → Loop Over Items 1  \n- Das ursprüngliche JSON wird **als einzelnes Item** verarbeitet.  \n- **Result1 & Result5:** Zeigen, dass das Array **nicht aufgeteilt** wurde, bevor es verarbeitet wird.\n\n#### Pfad „Geteiltes Array“ → Split Out → Loop Over Items 2  \n- Der **Split Out**-Knoten wandelt das `urls`-Array in einzelne Objekte um.\n- Der **Loop Over Items 2**-Knoten verarbeitet jede URL **nacheinander**.\n- Ein **Wait-Knoten** (1-Sekunden-Verzögerung) demonstriert **kontrollierte Ausführung**.\n- **Code-Knoten** verändern das JSON und fügen das Feld (`param1`) hinzu.\n- **Result2, Result3, Result4:** Zeigen die endgültige verarbeitete Ausgabe.\n\n### 2. Was du sehen wirst\n\n- **Result1 & Result5:** Das gesamte Array wird **als ein Item** verarbeitet, bevor es gesplittet wird.\n- **Result2, Result3, Result4:** Jede URL wird **einzeln** verarbeitet, nachdem sie aufgeteilt wurde.\n- **Wait Node:** Fügt **pro Item** im **Loop Over Items 2** eine **1-Sekunden-Pause** ein.\n\n---\n\n## Hinweise\n\n- Sticky Notes sind im Workflow enthalten **zur schnellen Orientierung**.\n- Der **Wait-Knoten** ist **optional** – entferne ihn bei Bedarf für schnellere Ausführung.\n- Diese Vorlage ist für **Einsteiger** gedacht, dient aber auch als **Grundbaustein** für komplexere Automatisierungen."
      },
      "typeVersion": 1
    },
    {
      "id": "53e7d23a-2a4f-4ada-aeb5-de128acf8625",
      "name": "Split Array of Strings into Array of Objects",
      "type": "n8n-nodes-base.splitOut",
      "position": [
        -20,
        380
      ],
      "parameters": {
        "options": {
          "destinationFieldName": "url"
        },
        "fieldToSplitOut": "urls"
      },
      "typeVersion": 1
    },
    {
      "id": "4910fec6-d600-43be-97b2-5050039db416",
      "name": "Sticky Note3",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        700
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 260,
        "content": "### Result4 zeigt, dass wir die Schleifenfunktion deaktivieren können, indem wir das Schleifenverhalten auf \"Einmal für alle Elemente ausführen\" setzen"
      },
      "typeVersion": 1
    },
    {
      "id": "f0e68b30-5341-4672-8d8e-7a24d894eb03",
      "name": "Sticky Note4",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        420
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 240,
        "content": "### Result3 zeigt, dass das Schleifen über Elemente in n8n-Knoten eingebaut ist"
      },
      "typeVersion": 1
    },
    {
      "id": "70a987b9-6a4a-49c3-a87c-0dd9cc1879ed",
      "name": "Result3",
      "type": "n8n-nodes-base.noOp",
      "notes": "Hier klicken, um das Ergebnis zu sehen",
      "position": [
        900,
        500
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },
    {
      "id": "9de5fac9-e987-4fb1-8f7f-b59af2985e5c",
      "name": "Result4",
      "type": "n8n-nodes-base.noOp",
      "notes": "Hier klicken, um das Ergebnis zu sehen",
      "position": [
        900,
        780
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },
    {
      "id": "d5fee847-7758-44ac-a270-6334dd81bb97",
      "name": "Sticky Note5",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        800,
        -640
      ],
      "parameters": {
        "color": 3,
        "width": 320,
        "height": 260,
        "content": "### Result5 zeigt, dass das String-Array von Code5 als ein einzelnes Element betrachtet wird. Das Verhalten ist also dasselbe wie bei Loop1"
      },
      "typeVersion": 1
    },
    {
      "id": "9a134620-4067-4c7a-8b0f-30e19c93a66c",
      "name": "Result5",
      "type": "n8n-nodes-base.noOp",
      "notes": "Hier klicken, um das Ergebnis zu sehen",
      "position": [
        880,
        -540
      ],
      "parameters": {},
      "notesInFlow": true,
      "typeVersion": 1
    },

    … (alle übrigen Knoten bleiben unverändert) …
  ],
  "active": false,
  "pinData": {},
  "settings": {
    "executionOrder": "v1"
  },
  "versionId": "e1eff37a-1ffd-4691-9560-eada5baab88d",
  "connections": {
    … (unverändert) …
  }
}
```

> **Hinweis**:  
> - Falls du **auch die Knoten-Namen** (z. B. „Result1“) übersetzen möchtest, müssen in `connections` gleichzeitig alle Referenzen angepasst werden.  
> - Die Ellipsen (`…`) im JSON oben bedeuten lediglich, dass dort nichts übersetzt werden musste – die entsprechenden Abschnitte bleiben exakt wie im Original.

### 3. Benutzer

übersetze nach deutsch: {
  "nodes": [
    {
      "parameters": {
        "content": "# N8N for Beginners: Looping Over Items\n\n## Description\n\nThis workflow is designed for **n8n beginners** to understand how n8n handles **looping (iteration)** over multiple items. It highlights two key behaviors:\n\n- **Built-In Looping:** By default, most n8n nodes iterate over each item in an input array.\n- **Explicit Looping:** The **Loop Over Items** node allows controlled iteration, enabling **custom batch processing** and multi-step workflows.\n\nThis workflow demonstrates the difference between processing an **unsplit array of strings (single item)** vs. **a split array (multiple items)**.\n\n---\n\n## Setup\n\n### 1. Input Data\n\nTo begin, **paste the following JSON** into the **Manual Trigger** node:\n\n```json\n{\n  \"urls\": [\n    \"https://www.reddit.com\",\n    \"https://www.n8n.io/\",\n    \"https://n8n.io/\",\n    \"https://supabase.com/\",\n    \"https://duckduckgo.com/\"\n  ]\n}\n```\n\nðŸ“Œ **Steps to Paste Data:**\n- **Double-click** the \"Manual Trigger\" node.\n- Click **\"Edit Output\"** (top-right corner).\n- Paste the JSON and **Save**.\n- The node **turns purple**, indicating that test data is pinned. \n\n---\n\n## Explanation of the n8n Nodes in the Workflow\n\n### Manual Trigger  \nThis node starts the workflow manually and sends test data.  \n**Documentation:** [Manual Trigger Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.manualtrigger/)\n\n### Split Out (Split Array of Strings into Array of Objects)  \nExtracts the `urls` array and splits it so that each URL becomes a separate JSON object.  \n**Documentation:** [Split Out Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitout/)\n\n### Loop Over Items (Loop Over Items 1)  \nDemonstrates how an **unsplit** array is treated as one item, processing it as a single unit.  \n**Documentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)\n\n### Loop Over Items (Loop Over Items 2)  \nProcesses the **split array** one item at a time. This demonstrates individual iteration and controlled looping.  \n**Documentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)\n\n### Wait Node  \nIntroduces a **1-second delay** per iteration to demonstrate sequential execution. This can be removed for faster performance.  \n**Documentation:** [Wait Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/)\n\n### Code Nodes (Add param1 to outputX)  \nEach Code node adds a constant field (`param1`) to the data, ensuring that every item gets enriched with the same parameter.  \n**Documentation:** [Code Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/)\n\n### NoOp Nodes (Result1, Result2, Result3, Result4, Result5)\nThese nodes display the output at different stages of the workflow for inspection.\n**Documentation:** [NoOp Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.noop/)\n\n\n\n---\n\n## Execution Details\n\n### 1. How the Workflow Runs\n\n- **Manual Trigger starts execution** with the pasted JSON data.\n- The workflow follows **two paths**:\n\n#### Unsplit Array Path â†’ Loop Over Items 1  \n- The original JSON is processed **as a single item**.  \n- **Result1 & Result5:** Show that the array was **not split** before processing.\n\n#### Split Array Path â†’ Split Out â†’ Loop Over Items 2  \n- The **Split Out** node converts the `urls` array into separate objects.\n- The **Loop Over Items 2** node processes each URL **one by one**.\n- A **Wait node** (1-second delay) demonstrates **controlled execution**.\n- **Code nodes** modify the JSON, adding the field (`param1`).\n- **Result2, Result3, Result4:** Display the final processed output.\n\n### 2. What You Will See\n\n- **Result1 & Result5:** The entire array is processed **as one item** before splitting.\n- **Result2, Result3, Result4:** Each URL is processed **individually** after being split.\n- **Wait Node:** Adds a **1-second delay per item** in **Loop Over Items 2**.\n\n---\n\n## Notes\n\n- Sticky notes are included in the workflow **for easy reference**.\n- The **Wait node** is **optional**â€”remove it for faster execution.\n- This template is structured for **beginners** but serves as a **building block** for more advanced automations.\n\n---\n\n",
        "height": 2480,
        "width": 1200
      },
      "id": "dc7b8775-213d-4d7f-8f66-3acb9bd5a2e1",
      "name": "Sticky Note2",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        -380,
        180
      ],
      "typeVersion": 1
    }
  ],
  "connections": {},
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "7e281f8fc9ee5315d924ba26778ef47420ca5a721b48dca4212fdb94b617bcdd"
  }
}

### 4. Assistent

Hier ist dein JSON-Snippet mit komplett ins Deutsche übersetztem Inhalt der Sticky-Note. Alle technischen Felder (IDs, Positionen, Verbindungen usw.) habe ich unverändert gelassen; nur **`parameters.content`** wurde lokalisiert.

```json
{
  "nodes": [
    {
      "parameters": {
        "content": "# n8n für Einsteiger: Schleifen über Elemente\n\n## Beschreibung\n\nDieser Workflow richtet sich an **n8n-Einsteiger**, um zu verstehen, wie n8n das **Schleifen (Iterieren)** über mehrere Elemente behandelt. Er hebt zwei wichtige Verhaltensweisen hervor:\n\n- **Eingebautes Schleifen:** Standardmäßig iterieren die meisten n8n-Knoten über jedes Element in einem Eingabe-Array.\n- **Explizites Schleifen:** Der **Loop Over Items**-Knoten ermöglicht eine gesteuerte Iteration, was **benutzerdefiniertes Batch-Processing** und mehrstufige Workflows erlaubt.\n\nDieser Workflow demonstriert den Unterschied zwischen der Verarbeitung eines **nicht aufgeteilten Arrays von Strings (ein einzelnes Element)** und eines **aufgeteilten Arrays (mehrere Elemente)**.\n\n---\n\n## Einrichtung\n\n### 1. Eingabedaten\n\nFüge zunächst **folgenden JSON-Code** in den **Manual Trigger**-Knoten ein:\n\n```json\n{\n  \"urls\": [\n    \"https://www.reddit.com\",\n    \"https://www.n8n.io/\",\n    \"https://n8n.io/\",\n    \"https://supabase.com/\",\n    \"https://duckduckgo.com/\"\n  ]\n}\n```\n\n📋 **So fügst du die Daten ein:**\n- **Doppelklicke** auf den \"Manual Trigger\"-Knoten.\n- Klicke oben rechts auf **\"Edit Output\"**.\n- Füge das JSON ein und **speichere**.\n- Der Knoten **färbt sich lila**, was zeigt, dass Testdaten angeheftet sind.\n\n---\n\n## Erläuterung der n8n-Knoten im Workflow\n\n### Manual Trigger  \nDieser Knoten startet den Workflow manuell und liefert Testdaten.  \n**Dokumentation:** [Manual Trigger Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.manualtrigger/)\n\n### Split Out (Array von Strings in Array von Objekten aufteilen)  \nExtrahiert das `urls`-Array und teilt es so auf, dass jede URL zu einem eigenen JSON-Objekt wird.  \n**Dokumentation:** [Split Out Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitout/)\n\n### Loop Over Items (Loop Over Items 1)  \nZeigt, wie ein **nicht aufgeteiltes** Array als ein einzelnes Element behandelt und als Einheit verarbeitet wird.  \n**Dokumentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)\n\n### Loop Over Items (Loop Over Items 2)  \nVerarbeitet das **aufgeteilte Array** Element für Element. Zeigt individuelle Iteration und kontrolliertes Schleifen.  \n**Dokumentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)\n\n### Wait Node  \nFügt eine **1-Sekunden-Verzögerung** pro Iteration hinzu, um sequentielle Ausführung zu zeigen. Kann für schnellere Abläufe entfernt werden.  \n**Dokumentation:** [Wait Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/)\n\n### Code-Knoten (Add param1 to outputX)  \nJeder Code-Knoten fügt das konstante Feld (`param1`) hinzu, sodass jedes Element um denselben Parameter erweitert wird.  \n**Dokumentation:** [Code Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/)\n\n### NoOp-Knoten (Result1, Result2, Result3, Result4, Result5)\nDiese Knoten zeigen die Ausgabe in verschiedenen Phasen des Workflows zur Kontrolle an.  \n**Dokumentation:** [NoOp Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.noop/)\n\n---\n\n## Ausführungsdetails\n\n### 1. So läuft der Workflow\n\n- **Manual Trigger** startet die Ausführung mit den eingefügten JSON-Daten.\n- Der Workflow folgt **zwei Pfaden**:\n\n#### Pfad „Ungeteiltes Array“ → Loop Over Items 1  \n- Das ursprüngliche JSON wird **als einzelnes Element** verarbeitet.  \n- **Result1 & Result5:** Zeigen, dass das Array **nicht aufgeteilt** wurde, bevor es verarbeitet wird.\n\n#### Pfad „Geteiltes Array“ → Split Out → Loop Over Items 2  \n- Der **Split Out**-Knoten wandelt das `urls`-Array in einzelne Objekte um.\n- Der **Loop Over Items 2**-Knoten verarbeitet jede URL **nacheinander**.\n- Ein **Wait-Knoten** (1-Sekunden-Verzögerung) demonstriert **kontrollierte Ausführung**.\n- **Code-Knoten** verändern das JSON und fügen das Feld (`param1`) hinzu.\n- **Result2, Result3, Result4:** Zeigen die endgültige verarbeitete Ausgabe.\n\n### 2. Was du sehen wirst\n\n- **Result1 & Result5:** Das gesamte Array wird **als ein Element** verarbeitet, bevor es aufgeteilt wird.\n- **Result2, Result3, Result4:** Jede URL wird **einzeln** verarbeitet, nachdem sie aufgeteilt wurde.\n- **Wait Node:** Fügt **pro Element** im **Loop Over Items 2** eine **1-Sekunden-Pause** ein.\n\n---\n\n## Hinweise\n\n- Sticky Notes sind im Workflow enthalten **zur schnellen Orientierung**.\n- Der **Wait-Knoten** ist **optional** – entferne ihn bei Bedarf für schnellere Ausführung.\n- Diese Vorlage ist für **Einsteiger** gedacht, dient aber auch als **Grundbaustein** für komplexere Automatisierungen.\n\n---\n",
        "height": 2480,
        "width": 1200
      },
      "id": "dc7b8775-213d-4d7f-8f66-3acb9bd5a2e1",
      "name": "Sticky Note2",
      "type": "n8n-nodes-base.stickyNote",
      "position": [
        -380,
        180
      ],
      "typeVersion": 1
    }
  ],
  "connections": {},
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "7e281f8fc9ee5315d924ba26778ef47420ca5a721b48dca4212fdb94b617bcdd"
  }
}
```

### 5. Benutzer

# N8N for Beginners: Looping Over Items

## Description

This workflow is designed for **n8n beginners** to understand how n8n handles **looping (iteration)** over multiple items. It highlights two key behaviors:

- **Built-In Looping:** By default, most n8n nodes iterate over each item in an input array.
- **Explicit Looping:** The **Loop Over Items** node allows controlled iteration, enabling **custom batch processing** and multi-step workflows.

This workflow demonstrates the difference between processing an **unsplit array of strings (single item)** vs. **a split array (multiple items)**.

---

## Setup

### 1. Input Data

To begin, **paste the following JSON** into the **Manual Trigger** node:

### 6. Assistent

# n8n für Einsteiger: Schleifen über Elemente

## Beschreibung

Dieser Workflow ist für **n8n-Anfänger** gedacht, um zu zeigen, wie n8n das **Schleifen (Iterieren)** über mehrere Elemente handhabt. Dabei werden zwei zentrale Verhaltensweisen hervorgehoben:

- **Eingebautes Schleifen:** Standardmäßig iterieren die meisten n8n-Knoten über jedes Element eines Eingabe-Arrays.  
- **Explizites Schleifen:** Mit dem Knoten **Loop Over Items** lässt sich die Iteration steuern, was **benutzerdefiniertes Batch-Processing** und mehrstufige Workflows ermöglicht.

Der Workflow zeigt den Unterschied zwischen der Verarbeitung eines **nicht aufgeteilten String-Arrays (ein einzelnes Element)** und eines **aufgeteilten Arrays (mehrere Elemente)**.

---

## Einrichtung

### 1. Eingabedaten

Beginne damit, **den folgenden JSON-Code** in den **Manual Trigger**-Knoten einzufügen:

### 7. Benutzer

Ÿ“Œ **Steps to Paste Data:**
- **Double-click** the "Manual Trigger" node.
- Click **"Edit Output"** (top-right corner).
- Paste the JSON and **Save**.
- The node **turns purple**, indicating that test data is pinned. 

---

## Explanation of the n8n Nodes in the Workflow

### Manual Trigger  
This node starts the workflow manually and sends test data.  
**Documentation:** [Manual Trigger Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.manualtrigger/)

### Split Out (Split Array of Strings into Array of Objects)  
Extracts the `urls` array and splits it so that each URL becomes a separate JSON object.  
**Documentation:** [Split Out Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitout/)

### Loop Over Items (Loop Over Items 1)  
Demonstrates how an **unsplit** array is treated as one item, processing it as a single unit.  
**Documentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)

### Loop Over Items (Loop Over Items 2)  
Processes the **split array** one item at a time. This demonstrates individual iteration and controlled looping.  
**Documentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)

### Wait Node  
Introduces a **1-second delay** per iteration to demonstrate sequential execution. This can be removed for faster performance.  
**Documentation:** [Wait Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/)

### Code Nodes (Add param1 to outputX)  
Each Code node adds a constant field (`param1`) to the data, ensuring that every item gets enriched with the same parameter.  
**Documentation:** [Code Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/)

### 8. Assistent

📋 **So fügst du die Daten ein:**  
- **Doppelklicke** auf den „Manual Trigger“-Knoten.  
- Klicke oben rechts auf **„Edit Output“**.  
- Füge das JSON ein und **speichere**.  
- Der Knoten färbt sich **lila**, was zeigt, dass Testdaten angeheftet sind.  

---

## Erläuterung der n8n-Knoten im Workflow

### Manual Trigger  
Dieser Knoten startet den Workflow manuell und liefert Testdaten.  
**Dokumentation:** [Manual Trigger Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.manualtrigger/)

### Split Out (Array von Strings in Array von Objekten aufteilen)  
Extrahiert das `urls`-Array und teilt es so auf, dass jede URL zu einem eigenen JSON-Objekt wird.  
**Dokumentation:** [Split Out Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitout/)

### Loop Over Items (Loop Over Items 1)  
Zeigt, wie ein **nicht aufgeteiltes** Array als ein einzelnes Element behandelt und als Einheit verarbeitet wird.  
**Dokumentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)

### Loop Over Items (Loop Over Items 2)  
Verarbeitet das **aufgeteilte Array** Element für Element. Demonstriert individuelle Iteration und kontrolliertes Schleifen.  
**Dokumentation:** [Loop Over Items Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/)

### Wait Node  
Fügt pro Iteration eine **1-Sekunden-Verzögerung** ein, um die sequentielle Ausführung zu demonstrieren. Kann für höhere Geschwindigkeit entfernt werden.  
**Dokumentation:** [Wait Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/)

### Code-Knoten (Add param1 to outputX)  
Jeder Code-Knoten fügt das konstante Feld (`param1`) hinzu, sodass jedes Element um denselben Parameter erweitert wird.  
**Dokumentation:** [Code Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/)

### 9. Benutzer

Jeder Code-Knoten fügt das konstante Feld (`param1`) hinzu, sodass jedes Element um denselben Parameter erweitert wird.
**Dokumentation:** [Code Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/)

### NoOp Nodes (Result1, Result2, Result3, Result4, Result5)
These nodes display the output at different stages of the workflow for inspection.
**Documentation:** [NoOp Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.noop/)



---

## Execution Details

### 1. How the Workflow Runs

- **Manual Trigger starts execution** with the pasted JSON data.
- The workflow follows **two paths**:

#### Unsplit Array Path â†’ Loop Over Items 1  
- The original JSON is processed **as a single item**.  
- **Result1 & Result5:** Show that the array was **not split** before processing.

#### Split Array Path â†’ Split Out â†’ Loop Over Items 2  
- The **Split Out** node converts the `urls` array into separate objects.
- The **Loop Over Items 2** node processes each URL **one by one**.
- A **Wait node** (1-second delay) demonstrates **controlled execution**.
- **Code nodes** modify the JSON, adding the field (`param1`).
- **Result2, Result3, Result4:** Display the final processed output.

### 2. What You Will See

- **Result1 & Result5:** The entire array is processed **as one item** before splitting.
- **Result2, Result3, Result4:** Each URL is processed **individually** after being split.
- **Wait Node:** Adds a **1-second delay per item** in **Loop Over Items 2**.

---

## Notes

- Sticky notes are included in the workflow **for easy reference**.
- The **Wait node** is **optional**â€”remove it for faster execution.
- This template is structured for **beginners** but serves as a **building block** for more advanced automations.

### 10. Assistent

### NoOp-Knoten (Result1, Result2, Result3, Result4, Result5)  
Diese Knoten zeigen die Ausgabe in verschiedenen Phasen des Workflows zur Kontrolle an.  
**Dokumentation:** [NoOp Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.noop/)

---

## Ausführungs­details

### 1. So läuft der Workflow

- **Manual Trigger** startet die Ausführung mit den eingefügten JSON-Daten.  
- Der Workflow folgt **zwei Pfaden**:

#### Pfad „Ungeteiltes Array“ → Loop Over Items 1  
- Das ursprüngliche JSON wird **als einzelnes Element** verarbeitet.  
- **Result1 & Result5:** zeigen, dass das Array **nicht aufgeteilt** wurde, bevor es verarbeitet wird.

#### Pfad „Geteiltes Array“ → Split Out → Loop Over Items 2  
- Der **Split Out**-Knoten wandelt das `urls`-Array in separate Objekte um.  
- Der **Loop Over Items 2**-Knoten verarbeitet jede URL **nacheinander**.  
- Ein **Wait-Knoten** (1-Sekunden-Verzögerung) demonstriert die **kontrollierte Ausführung**.  
- **Code-Knoten** ergänzen das JSON um das Feld (`param1`).  
- **Result2, Result3, Result4:** zeigen die endgültig verarbeitete Ausgabe.

### 2. Was du sehen wirst

- **Result1 & Result5:** Das gesamte Array wird **als ein Element** verarbeitet, bevor es aufgeteilt wird.  
- **Result2, Result3, Result4:** Jede URL wird **einzeln** verarbeitet, nachdem sie aufgeteilt wurde.  
- **Wait-Knoten:** Fügt **pro Element** im **Loop Over Items 2** eine **1-Sekunden-Pause** ein.

---

## Hinweise

- Sticky Notes sind im Workflow **zur schnellen Orientierung** enthalten.  
- Der **Wait-Knoten** ist **optional** – entferne ihn für schnellere Ausführung.  
- Diese Vorlage ist für **Einsteiger** gedacht, dient aber auch als **Grundbaustein** für weiterführende Automatisierungen.
