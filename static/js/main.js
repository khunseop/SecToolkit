import { switchCategory, showTool, copyToClipboard, copyTextToClipboard } from './modules/ui.js';
import { transform, copyAnalysisReport, initTextCounter } from './modules/transformer.js';
import { initAnalyzer, loadUnits, doConvert, beautifyJson, uploadHar } from './modules/analyzer.js';
import { initPac, savePacGroup, selectPacGroup, deletePacGroup, testProdPac, comparePac, renderDiff, copyFullReport, searchInPac } from './modules/pac.js';
import { refreshSystemInfo, doDnsLookup } from './modules/system.js';

// Expose to window for HTML onclick handlers (due to ES6 module scoping)
window.switchCategory = switchCategory;
window.showTool = showTool;
window.copyToClipboard = copyToClipboard;
window.copyTextToClipboard = copyTextToClipboard;

window.transform = transform;
window.copyAnalysisReport = copyAnalysisReport;

window.loadUnits = loadUnits;
window.doConvert = doConvert;
window.beautifyJson = beautifyJson;
window.uploadHar = uploadHar;

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

// Initialize modules
document.addEventListener('DOMContentLoaded', () => {
    initTextCounter();
    initAnalyzer();
    initPac();
    refreshSystemInfo();
});
