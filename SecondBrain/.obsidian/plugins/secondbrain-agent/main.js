const obsidian = require("obsidian");

const DEFAULT_SETTINGS = {
  dashboardUrl: "http://localhost:8765",
  apiUrl: "http://localhost:8787"
};

module.exports = class SecondBrainAgentPlugin extends obsidian.Plugin {
  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());

    this.addRibbonIcon("brain", "SecondBrain Agent", () => {
      new obsidian.Notice("SecondBrain Agent");
      window.open(this.settings.dashboardUrl);
    });

    this.addCommand({
      id: "open-secondbrain-dashboard",
      name: "Open SecondBrain Dashboard",
      callback: () => window.open(this.settings.dashboardUrl)
    });

    this.addCommand({
      id: "open-secondbrain-api-status",
      name: "Open SecondBrain API Status",
      callback: () => window.open(this.settings.apiUrl + "/status")
    });

    this.addCommand({
      id: "run-secondbrain-import",
      name: "Run Import",
      callback: async () => this.callApi("/run/import", "Import gestartet")
    });

    this.addCommand({
      id: "run-secondbrain-intelligence",
      name: "Run Intelligence Cycle",
      callback: async () => this.callApi("/run/intelligence", "Intelligence Cycle gestartet")
    });

    this.addCommand({
      id: "run-secondbrain-governance",
      name: "Run Governance",
      callback: async () => this.callApi("/run/governance", "Governance gestartet")
    });

    this.addCommand({
      id: "show-secondbrain-os-cycle-command",
      name: "Show SecondBrain OS Cycle Command",
      callback: () => {
        new obsidian.Notice("PowerShell: cd H:\\SecondBrainAgent\\SecondBrain-Agent && python scripts\\run_secondbrain_os_cycle.py", 10000);
      }
    });

    this.addSettingTab(new SecondBrainSettingTab(this.app, this));
  }

  async callApi(path, successMessage) {
    try {
      const response = await fetch(this.settings.apiUrl + path);
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      new obsidian.Notice(successMessage);
    } catch (e) {
      new obsidian.Notice("SecondBrain API nicht erreichbar. Starte: python scripts\\rest_api.py", 8000);
    }
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  onunload() {}
};

class SecondBrainSettingTab extends obsidian.PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const {containerEl} = this;
    containerEl.empty();

    containerEl.createEl("h2", {text: "SecondBrain Agent Settings"});

    new obsidian.Setting(containerEl)
      .setName("Dashboard URL")
      .setDesc("Lokales Dashboard des SecondBrain-Agent.")
      .addText(text => text
        .setPlaceholder("http://localhost:8765")
        .setValue(this.plugin.settings.dashboardUrl)
        .onChange(async (value) => {
          this.plugin.settings.dashboardUrl = value;
          await this.plugin.saveSettings();
        }));

    new obsidian.Setting(containerEl)
      .setName("API URL")
      .setDesc("Lokale REST API des SecondBrain-Agent.")
      .addText(text => text
        .setPlaceholder("http://localhost:8787")
        .setValue(this.plugin.settings.apiUrl)
        .onChange(async (value) => {
          this.plugin.settings.apiUrl = value;
          await this.plugin.saveSettings();
        }));

    containerEl.createEl("hr");
    containerEl.createEl("p", {
      text: "REST API starten: cd H:\\SecondBrainAgent\\SecondBrain-Agent && python scripts\\rest_api.py"
    });
  }
}