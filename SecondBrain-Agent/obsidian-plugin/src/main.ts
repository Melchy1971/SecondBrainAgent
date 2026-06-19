import { App, Notice, Plugin, PluginSettingTab, Setting } from "obsidian";

interface SecondBrainSettings {
  dashboardUrl: string;
  apiUrl: string;
}

const DEFAULT_SETTINGS: SecondBrainSettings = {
  dashboardUrl: "http://localhost:8765",
  apiUrl: "http://localhost:8787"
};

export default class SecondBrainAgentPlugin extends Plugin {
  settings: SecondBrainSettings;

  async onload() {
    await this.loadSettings();

    this.addRibbonIcon("brain", "SecondBrain OS", () => {
      new Notice("SecondBrain OS");
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
      id: "run-secondbrain-os-cycle",
      name: "Run SecondBrain OS Cycle",
      callback: async () => {
        new Notice("SecondBrain OS Cycle über PowerShell starten: python scripts/run_secondbrain_os_cycle.py");
      }
    });

    this.addSettingTab(new SecondBrainSettingTab(this.app, this));
  }

  async callApi(path: string, success: string) {
    try {
      await fetch(this.settings.apiUrl + path);
      new Notice(success);
    } catch (e) {
      new Notice("SecondBrain API nicht erreichbar.");
    }
  }

  onunload() {}

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}

class SecondBrainSettingTab extends PluginSettingTab {
  plugin: SecondBrainAgentPlugin;

  constructor(app: App, plugin: SecondBrainAgentPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const {containerEl} = this;
    containerEl.empty();

    containerEl.createEl("h2", {text: "SecondBrain Agent Settings"});

    new Setting(containerEl)
      .setName("Dashboard URL")
      .addText(text => text
        .setValue(this.plugin.settings.dashboardUrl)
        .onChange(async (value) => {
          this.plugin.settings.dashboardUrl = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName("API URL")
      .addText(text => text
        .setValue(this.plugin.settings.apiUrl)
        .onChange(async (value) => {
          this.plugin.settings.apiUrl = value;
          await this.plugin.saveSettings();
        }));
  }
}
