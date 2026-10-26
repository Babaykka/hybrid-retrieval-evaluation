import fs from 'node:fs/promises';
import {pathToFileURL} from 'node:url';

const root = '.';
const build = root + '/presentation_2026/review_2026-10-12/build/clarity';
const skill = (process.env.PRESENTATIONS_SKILL||'');
process.env.RUNTIME_NODE_MODULES = (process.env.RUNTIME_NODE_MODULES||'');
const {finalizePresentation} = await import(pathToFileURL(skill + '/container_tools/artifact_tool_utils.mjs'));
await fs.mkdir(build + '/validated', {recursive: true});
const tableOwners = [2,3,4,17,21,22,23,24,25];
const revision = process.argv[2] || 'v1';
const result = await finalizePresentation({
  workspaceDir: root,
  candidatePath: build + '/candidate.pptx',
  finalPath: build + `/validated/final_${revision}.pptx`,
  pythonExecutable: (process.env.PYTHON||'python3'),
  integrityValidatorPath: skill + '/container_tools/inspect_presentation_package_integrity.py',
  layoutValidatorPath: skill + '/container_tools/inspect_presentation_layout_geometry.py',
  explicitTotalSlideCount: 26,
  requiredNativeTableOwnerSlides: tableOwners,
  requiredNativeChartOwnerSlides: [8,10,13,15,16],
  requiredEmbeddedWorkbookChartOwnerSlides: [8,10,13,15,16],
  materializeLiteralChartWorkbooks: false,
  layoutArgs: ['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n => ['--require-native-table-slide',String(n)])],
  fontPolicy: {basis:'reference',families:['Arial'],referencePath:root+'/DAMDID_2026_Правки_к_докладу/DAMDID_2026_Презентация_RU.pptx',referenceSha256:'aab136cff068a089406bb52d54b7e2a78b01dac8e65e833c180e8b47467307d8'},
  verifyArtifactToolImport: true,
  receiptPath: build + `/validation_${revision}.json`
});
console.log(JSON.stringify(result, null, 2));
