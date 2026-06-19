const { Notice, Plugin, PluginSettingTab, Setting } = require("obsidian");

const DEFAULT_SETTINGS = {
  dashboardUrl: "http://localhost:8765",
  apiUrl: "http://localhost:8787"
};

module.exports = class SecondBrainAgentPlugin extends Plugin {
  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());

    this.addRibbonIcon("brain", "SecondBrain Agent", () => {
      new Notice("SecondBrain Agent");
      window.open(this.settings.dashboardUrl);
    });

    this.addCommand({
      id: "open-secondbrain-dashboard",
      name: "Open Dashboard",
      callback: () => window.open(this.settings.dashboardUrl)
    });

    this.addCommand({
      id: "open-secondbrain-api-status",
      name: "Open API Status",
      callback: () => window.open(this.settings.apiUrl + "/status")
    });

    this.addCommand({
      id: "run-secondbrain-import",
      name: "Run Import via Local API",
      callback: async () => {
        try {
          await fetch(this.settings.apiUrl + "/run/import");
          new Notice("SecondBrain Import gestartet.");
        } catch (e) {
          new Notice("SecondBrain API nicht erreichbar.");
        }
      }
    });

    this.addCommand({
      id: "run-secondbrain-intelligence",
      name: "Run Intelligence Cycle via Local API",
      callback: async () => {
        try {
          await fetch(this.settings.apiUrl + "/run/intelligence");
          new Notice("SecondBrain Intelligence Cycle gestartet.");
        } catch (e) {
          new Notice("SecondBrain API nicht erreichbar.");
        }
      }
    });

    this.addSettingTab(new SecondBrainSettingTab(this.app, this));
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
};

class SecondBrainSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl("h2", { text: "SecondBrain Agent Settings" });

    new Setting(containerEl)
      .setName("Dashboard URL")
      .setDesc("Lokales Dashboard")
      .addText(text => text
        .setPlaceholder("http://localhost:8765")
        .setValue(this.plugin.settings.dashboardUrl)
        .onChange(async (value) => {
          this.plugin.settings.dashboardUrl = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName("API URL")
      .setDesc("Lokale REST API")
      .addText(text => text
        .setPlaceholder("http://localhost:8787")
        .setValue(this.plugin.settings.apiUrl)
        .onChange(async (value) => {
          this.plugin.settings.apiUrl = value;
          await this.plugin.saveSettings();
        }));
  }
}
