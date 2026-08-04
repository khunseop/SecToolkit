import { switchCategory, showTool, copyToClipboard, copyTextToClipboard } from './modules/ui.js';
import { transform, transformIpToSql, copyAnalysisReport, initTextCounter } from './modules/transformer.js';
import { initAnalyzer, loadUnits, doConvert, beautifyJson, uploadHar, findIpIntersections } from './modules/analyzer.js';
import { initPac, savePacGroup, selectPacGroup, deletePacGroup, testProdPac, comparePac, renderDiff, copyFullReport, searchInPac } from './modules/pac.js';
import { refreshSystemInfo } from './modules/system.js';
import { doDnsLookup, refreshDnsInfo, initDns } from './modules/dns.js';
import { generatePaCommand, updatePaFormVisibility, savePaDefaults, initPaloAlto, addGridRow, generateBulkFromGrid, uploadExcelAndGenerate } from './modules/paloalto.js';

// Expose to window for HTML onclick handlers (due to ES6 module scoping)
window.switchCategory = switchCategory;
window.showTool = showTool;
window.copyToClipboard = copyToClipboard;
window.copyTextToClipboard = copyTextToClipboard;

window.transform = transform;
window.transformIpToSql = transformIpToSql;
window.copyAnalysisReport = copyAnalysisReport;

window.loadUnits = loadUnits;
window.doConvert = doConvert;
window.beautifyJson = beautifyJson;
window.uploadHar = uploadHar;
window.findIpIntersections = findIpIntersections;

window.savePacGroup = savePacGroup;
window.selectPacGroup = selectPacGroup;
window.deletePacGroup = deletePacGroup;
window.testProdPac = testProdPac;
window.comparePac = comparePac;
window.renderDiff = renderDiff;
window.copyFullReport = copyFullReport;
window.searchInPac = searchInPac;

window.refreshSystemInfo = refreshSystemInfo;
window.doDnsLookup = doDnsLookup;
window.refreshDnsInfo = refreshDnsInfo;

window.generatePaCommand = generatePaCommand;
window.updatePaFormVisibility = updatePaFormVisibility;
window.savePaDefaults = savePaDefaults;
window.addGridRow = addGridRow;
window.generateBulkFromGrid = generateBulkFromGrid;
window.uploadExcelAndGenerate = uploadExcelAndGenerate;

// Initialize modules
document.addEventListener('DOMContentLoaded', () => {
    initTextCounter();
    initAnalyzer();
    initPac();
    initDns();
    refreshSystemInfo();
    initPaloAlto();
});
