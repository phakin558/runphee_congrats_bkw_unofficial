# GAS / Google Sheets setup

## 1) Sheet

Create a sheet named `Students` with this header row:

`ปีที่จบ | สถานที่เรียนต่อ | ประเภท | URL รูปภาพนักเรียน | URL โลโก้มหาวิทยาลัย | สถานะ | Timestamp | id | คณะ`

Rows with an empty status are treated as `on` when read. New rows are always written as `on`.

## 2) Apps Script

Copy `Code.gs` into the Apps Script project bound to the spreadsheet (or a standalone project). In Project Settings > Script properties, add:

- `SPREADSHEET_ID`: the spreadsheet ID
- `SHEET_NAME`: `Sheet1` (optional; this is the tab name at the bottom of the spreadsheet)
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_UPLOAD_PRESET`: an unsigned upload preset

Deploy as a Web app, execute as the owner, and allow the intended users to access it. Put the deployed `/exec` URL into `public/data_sources.json` as `gasWebAppUrl`.

## 3) Existing Dashboard form

Import the functions from `src/studentApi.js` and use this flow:

```js
const universities = await getUniqueUniversities();
const existing = findUniversity(universities, universityInput.value);
const studentImageFile = await fileToWebp(studentImageInput.files[0], .8);
const logoFile = existing ? null : await fileToWebp(logoInput.files[0], .8);

await addStudentData({
  year: yearInput.value,
  university: universityInput.value,
  type: typeInput.value,
  studentImageFile,
  logoFile,
  logoUrl: existing?.logoUrl || ''
});

await softDeleteStudent(rowIndex); // rowIndex comes from GAS, not the array index
```

For a new university, require `logoInput.files[0]` before calling `addStudentData`. For an existing university, use the returned `logoUrl` and do not upload a new logo.
