import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';

const root = '.';
const build = root + '/presentation_2026/audit_2026-10-13';
const skill = (process.env.PRESENTATIONS_SKILL||'');
const reference = root + '/DAMDID_2026_Уточненная_версия 2/DAMDID_2026_Презентация_RU.pptx';
process.env.RUNTIME_NODE_MODULES = (process.env.RUNTIME_NODE_MODULES||'');
const {finalizePresentation} = await import(pathToFileURL(skill + '/container_tools/artifact_tool_utils.mjs'));
const tableOwners = [2,3,4,17,21,22,23,24,25];
const result = await finalizePresentation({
  workspaceDir: root,
  candidatePath: build + '/candidate_refreshed.pptx',
  finalPath: root + '/DAMDID_2026_Проверено_13-10/DAMDID_2026_Презентация_RU.pptx',
  pythonExecutable: (process.env.PYTHON||'python3'),
  integrityValidatorPath: skill + '/container_tools/inspect_presentation_package_integrity.py',
  layoutValidatorPath: skill + '/container_tools/inspect_presentation_layout_geometry.py',
  explicitTotalSlideCount: 26,
  requiredNativeTableOwnerSlides: tableOwners,
  requiredNativeChartOwnerSlides: [8,10,13,15,16],
  requiredEmbeddedWorkbookChartOwnerSlides: [8,10,13,15,16],
  materializeLiteralChartWorkbooks: false,
  layoutArgs: ['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n => ['--require-native-table-slide',String(n)])],
  fontPolicy: {basis:'reference',families:['Arial'],referencePath:reference,referenceSha256:createHash('sha256').update(await fs.readFile(reference)).digest('hex')},
  verifyArtifactToolImport: true,
  receiptPath: build + '/validation.json'
});
console.log(JSON.stringify(result, null, 2));
