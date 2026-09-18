/**
 * TenderPulse 4IR - SparrowGenie-Style Contractor Institutional Knowledge Vault
 * Preserves institutional memory: corporate credentials, 5-year audited financials,
 * registered key personnel, equipment fleet, and past completion certificates.
 */

class ContractorKnowledgeVault {
  constructor() {
    this.storageKey = "tp_contractor_vault_v1";
    this.vault = this.loadVault();
  }

  loadVault() {
    try {
      const saved = localStorage.getItem(this.storageKey);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.warn("Using default vault seed:", e);
    }

    return {
      company: {
        name: "Prime Infrastructure & Construction Ltd.",
        shortName: "Prime Infra",
        tradeLicense: "TRAD/DSCC/019482/2021",
        tinNumber: "4920-1928-3019",
        vatReg: "001928471-0101",
        cptuEnlistment: "Class-1 Super-Special (PWD & RHD Enlisted)",
        egpUserId: "BDR-789042",
        registeredAddress: "Level 14, Sena Kalyan Bhaban, Motijheel C/A, Dhaka-1000",
        managingDirector: "Engr. M. A. Karim, FIEB"
      },
      financials: {
        auditedTurnover: [
          { fiscalYear: "2024-2025", amount: 485000000, auditor: "A. Qasem & Co. Chartered Accountants" },
          { fiscalYear: "2023-2024", amount: 442000000, auditor: "A. Qasem & Co. Chartered Accountants" },
          { fiscalYear: "2022-2023", amount: 512000000, auditor: "Rahman Rahman Huq (KPMG BD)" },
          { fiscalYear: "2021-2022", amount: 395000000, auditor: "Rahman Rahman Huq (KPMG BD)" },
          { fiscalYear: "2020-2021", amount: 360000000, auditor: "Hoda Vasi Chowdhury & Co." }
        ],
        peakAnnualTurnover: 512000000, // 51.2 Cr
        averageTurnover: 438800000,   // 43.88 Cr
        sanctionedCreditLines: [
          { bank: "Prime Bank PLC", branch: "Motijheel Corporate", facility: "e-GP SpeedCredit", amount: 250000000, expiry: "2027-06-30" },
          { bank: "BRAC Bank PLC", branch: "Gulshan Head Office", facility: "InfraConstruct Line", amount: 180000000, expiry: "2026-12-31" }
        ],
        totalCreditLimit: 430000000,  // 43.0 Cr
        activeCommitmentsB: 120000000 // 12.0 Cr on-going
      },
      personnel: [
        {
          id: "EMP-01",
          name: "Engr. Md. Rafiqul Islam, FIEB",
          role: "Project Manager (Civil)",
          degree: "B.Sc. in Civil Engineering (BUET)",
          iebNo: "F-12948",
          totalExp: "16 Years",
          similarExp: "11 Years in Highway Bridges & Flyovers",
          nid: "19802692019284712",
          status: "Available"
        },
        {
          id: "EMP-02",
          name: "Engr. Tanvir Chowdhury, MIEB",
          role: "Senior Bridge / Structural Engineer",
          degree: "M.Sc. in Structural Engineering (CUET)",
          iebNo: "M-19402",
          totalExp: "12 Years",
          similarExp: "8 Years in Pre-Stressed Concrete (PSC)",
          nid: "19852692019481729",
          status: "Available"
        },
        {
          id: "EMP-03",
          name: "Engr. Sabrina Yasmin",
          role: "Quality Assurance (QA/QC) Engineer",
          degree: "B.Sc. in Civil Engineering (AUST)",
          iebNo: "M-22410",
          totalExp: "9 Years",
          similarExp: "6 Years in Heavy Concrete Testing",
          nid: "19902692019882711",
          status: "Available"
        },
        {
          id: "EMP-04",
          name: "Md. Enamul Haque",
          role: "Senior Surveyor",
          degree: "Diploma in Civil & Surveying Technology",
          iebNo: "Dip-7841",
          totalExp: "8 Years",
          similarExp: "Total Station, DGPS & Drone Topography",
          nid: "19882692011928471",
          status: "Available"
        }
      ],
      equipment: [
        {
          id: "EQ-01",
          name: "Hydraulic Rotary Drilling Rig (Bore Piling)",
          model: "Bauer BG 24 H",
          capacity: "1500mm dia / 60m depth",
          ownership: "Owned (Reg #DHK-ENG-402)",
          status: "Operational"
        },
        {
          id: "EQ-02",
          name: "Heavy Duty Mobile Hydraulic Crane",
          model: "SANY STC500",
          capacity: "50 Tonne",
          ownership: "Owned (Reg #DHK-ENG-219)",
          status: "Operational"
        },
        {
          id: "EQ-03",
          name: "Automated Concrete Batching Plant",
          model: "Schwing Stetter CP-45",
          capacity: "45 m3/hr with Aggregate Chiller",
          ownership: "Owned (Installed Base)",
          status: "Operational"
        },
        {
          id: "EQ-04",
          name: "Transit Mixer Trucks",
          model: "Ashok Leyland 2518",
          capacity: "4 Units x 6 m3 capacity",
          ownership: "Owned (Fleet Reg DHK-METRO-SH)",
          status: "Operational"
        },
        {
          id: "EQ-05",
          name: "PSC Pre-Stressing Hydraulic Jacks",
          model: "Freyssinet 300T Multistrand",
          capacity: "2 Units x 300 Tonne calibrated",
          ownership: "Owned (Calibrated BUET 2026)",
          status: "Operational"
        }
      ],
      pastProjects: [
        {
          projectTitle: "Construction of 3-Lane RCC Girder Bridge over Meghna Tributary, Narsingdi",
          client: "Roads and Highways Department (RHD)",
          xenOffice: "Executive Engineer, RHD Narsingdi Division",
          value: 385000000, // 38.5 Cr
          completedDate: "2024-11-20",
          certificateRef: "RHD/NAR/CERT/2024/991",
          status: "Completed (Satisfactory Certificate Attached)"
        },
        {
          projectTitle: "Vertical Extension of 8-Storied Academic Building with Substation, Gazipur",
          client: "Education Engineering Department (EED)",
          xenOffice: "Executive Engineer, EED Dhaka Metro",
          value: 260000000, // 26.0 Cr
          completedDate: "2023-08-15",
          certificateRef: "EED/DHK/2023/W-102",
          status: "Completed (Satisfactory Certificate Attached)"
        }
      ]
    };
  }

  saveVault(updatedVault) {
    this.vault = updatedVault;
    localStorage.setItem(this.storageKey, JSON.stringify(this.vault));
  }

  getVaultData() {
    return this.vault;
  }

  getProfile() {
    const data = this.getVaultData();
    return {
      name: data.company ? data.company.name : "Prime Infrastructure & Construction Ltd.",
      peakTurnoverBDT: data.financials ? data.financials.peakAnnualTurnover : 512000000,
      liquidAssetsBDT: 150000000,
      creditLimitBDT: data.financials ? data.financials.totalCreditLimit : 430000000,
      commitmentsB: data.financials ? data.financials.activeCommitmentsB : 120000000,
      company: data.company,
      financials: data.financials,
      personnel: data.personnel,
      equipment: data.equipment,
      pastProjects: data.pastProjects
    };
  }
}

// Global Singleton
window.contractorVault = new ContractorKnowledgeVault();
