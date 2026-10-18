# Vendor CAD models and maker documents (index)

The files live in the main checkout's `cad/vendor/<maker>/<pn>/` and are **not committed** (gitignored, R67; only this
index is tracked). DECISIONS R163: every bought part in a CAD assembly is the maker's own model; a community model only
after Dispatch gives the URL; anything built from a data sheet says so here, in its file name, and cites the sheet (Dispatch Q2 = A, 2026-10-18).

**How the files were fetched:** te.com, littelfuse.com and eaton.com refuse plain shell downloads (TE 403, Littelfuse 403,
Eaton connection reset / timeout, tested 2026-10-18). The files below were fetched once through the in-app browser on the maker's
own site; that path left Save dialogs open on Dan's screen and is no longer used. A new file from these makers is listed for
Dan instead (Dispatch 2026-10-18).
The two MCP 2.8 models (1-968851-1, 1-968849-1, 2026-10-18) were read from TE's own document URL inside a te.com page and handed
straight to a local listener on this PC (no Save dialog, nothing clicked); same files, byte for byte, as TE serves.

## 3D models (official maker STEP)

| PN | Maker | What | Source | File |
|---|---|---|---|---|
| 880398-2 | TE Connectivity | Fuse contact 2.8, 1-2.5 mm2 (mini fuse sockets; R85 C4) | official 3D STEP ([product page](https://www.te.com/en/product-880398-2.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_880398-2&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=880398-2)) | `te/880398-2/c-880398-2-t-3d.stp` |
| 1241388-2 | TE Connectivity | MCP 2.8K receptacle 0.5-1 mm2 | official 3D STEP ([product page](https://www.te.com/en/product-1241388-2.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=1241388-2&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=1241388-2)) | `te/1241388-2/c-1241388-2-c6-3d.stp` |
| 1241390-1 | TE Connectivity | MCP 2.8K receptacle 1.5-2.5 mm2 | official 3D STEP ([product page](https://www.te.com/en/product-1241390-1.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=1241390-1&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=1241390-1)) | `te/1241390-1/c-1241390-1-c6-3d.stp` |
| 42281-1 | TE Connectivity | FASTON .250 receptacle 18-14 AWG | official 3D STEP ([product page](https://www.te.com/en/product-42281-1.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_42281-1&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=42281-1)) | `te/42281-1/c-42281-1-dj-3d.stp` |
| 280919-2 | TE Connectivity | FASTIN-FASTON .187 receptacle 20-15 AWG | official 3D STEP ([product page](https://www.te.com/en/product-280919-2.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_280919-2&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=280919-2)) | `te/280919-2/c-280919-2-m-3d.stp` |
| 280755-4 | TE Connectivity | FASTON .375 receptacle 10-7 AWG | official 3D STEP ([product page](https://www.te.com/en/product-280755-4.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_280755-4&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=280755-4)) | `te/280755-4/c-280755-4-l-3d.stp` |
| 280756-4 | TE Connectivity | FASTON .375 receptacle 12-10 AWG | official 3D STEP ([product page](https://www.te.com/en/product-280756-4.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_280756-4&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=280756-4)) | `te/280756-4/c-280756-4-p-3d.stp` |
| 62998-2 | TE Connectivity | FASTON .250 receptacle 10-8 AWG | official 3D STEP ([product page](https://www.te.com/en/product-62998-2.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_62998-2&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=62998-2)) | `te/62998-2/c-62998-2-w-3d.stp` |
| 1-968851-1 | TE Connectivity | MCP 2.8 receptacle 16 / 14 AWG - mini fuse sockets (R166) | official 3D STEP ([product page](https://www.te.com/en/product-1-968851-1.html); drawings 968851 B4, 1355036 J15; application spec 114-18148 Rev D1) | `te/1-968851-1/c-1-968851-1-e-3d.stp` |
| 1-968849-1 | TE Connectivity | MCP 2.8 receptacle 20 / 18 AWG - mini fuse sockets (R166) | official 3D STEP ([product page](https://www.te.com/en/product-1-968849-1.html); drawings 968849 B4, 1355036 J15; application spec 114-18148 Rev D1) | `te/1-968849-1/c-1-968849-1-j3-3d.stp` |
| 1-1414147-0 | TE Connectivity | Power Relay F7 (Maxi ISO), 1 form A - k_efi / k_str / k_fan | official 3D STEP ([product page](https://www.te.com/en/product-1-1414147-0.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_1-1414147-0&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=1-1414147-0)) | `te/1-1414147-0/c-1-1414147-0-a-3d.stp` |
| 1-1393304-0 | TE Connectivity | Power Relay F7 (Maxi ISO), bracket - k_fan2 / power | official 3D STEP ([product page](https://www.te.com/en/product-1-1393304-0.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_1-1393304-0&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=1-1393304-0)) | `te/1-1393304-0/c-1-1393304-0-a-3d.stp` |
| 1-1414687-0 | TE Connectivity | Heater relay k_htr, 1 form C | official 3D STEP ([product page](https://www.te.com/en/product-1-1414687-0.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_1-1414687-0&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=1-1414687-0)) | `te/1-1414687-0/c-1-1414687-0-o-3d.stp` |
| 4-1904124-2 | TE Connectivity | Micro relay k_etb | official 3D STEP ([product page](https://www.te.com/en/product-4-1904124-2.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_4-1904124-2&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=4-1904124-2)) | `te/4-1904124-2/c-4-1904124-2-a-3d.stp` |
| 4-1904124-3 | TE Connectivity | Micro relay horn | official 3D STEP ([product page](https://www.te.com/en/product-4-1904124-3.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_4-1904124-3&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=4-1904124-3)) | `te/4-1904124-3/c-4-1904124-3-a-3d.stp` |
| 5-1393292-8 | TE Connectivity | Micro relay HEAD LH / HEAD RH | official 3D STEP ([product page](https://www.te.com/en/product-5-1393292-8.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_5-1393292-8&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=5-1393292-8)) | `te/5-1393292-8/c-5-1393292-8-o-3d.stp` |
| 6-1419137-4 | TE Connectivity | Micro relay k_acc / k_eps_en / k_rev | official 3D STEP ([product page](https://www.te.com/en/product-6-1419137-4.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_6-1419137-4&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=6-1419137-4)) | `te/6-1419137-4/c-6-1419137-4-o-3d.stp` |
| 1416010-1 | TE Connectivity | HCR150 fuel pump relay k_fp (battery block) | official 3D STEP ([product page](https://www.te.com/en/product-1416010-1.html), [file](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=CVM_1416010-1&DocType=Customer%20View%20Model&DocLang=English&DocFormat=3d_stp.zip&PartCntxt=1416010-1)) | `te/1416010-1/c-1416010-1-a-3d.stp` |

## Parts with no official maker model (built from the data sheet)

| PN | Maker | What | Model | Built from | Where Dan can grab an official model |
|---|---|---|---|---|---|
| ATM-2 / -5 / -7-1/2 / -10 / -15 / -20 | Eaton Bussmann | Mini blade fuses: LOGIC, POWER ACPS 10 A | `eaton/ATM/ATM_mini-blade_built-from-Littelfuse-297-ds-2024-09-27-p2.step` | Littelfuse MINI 297 32 V data sheet rev 09/27/2024 p.2 (ISO 8820-3 mini: body 10.9 x 3.8 x 8.8, blades 7.5 long, 2.8 x 0.8, 10.9 over both blades); height 16.3 matches Eaton's 0.642 in. Tip chamfer drawn, not dimensioned: UNVERIFIED | none from Eaton (SKU page https://www.eaton.com/us/en-us/skuPage.ATM-10.html has no CAD). Littelfuse MINI 3D models are behind a form: https://info.littelfuse.com/ (search "MINI 3D model") |
| AMI-30 / -40 / -50 / -60 | Eaton Bussmann | POWER outputs, battery block FP 40A | `eaton/AMI/AMI_bolt-in_built-from-Bussmann-AMI-ds-p34.step` | Bussmann AMI series sheet p.34 (`eaton/specs/bussmann-ami-series-p34.pdf`): 41.0 over the ears, holes D5.5 at 30.0, body 16.0 x 12.0 x 6.0, ears 9.5 x 0.8. Ear end radius drawn, not dimensioned: UNVERIFIED | none found (SnapEDA lists AMI-150 on request only: https://www.snapeda.com/parts/AMI-150/BUSSMANN%20/%20EATON/view-part/ - community, ask Dispatch first) |
| MAXI fuse, mini ISO relay | - | - | - | not used in any fuse box parts list (`cad/fusebox/fusebox-parts-*.csv`, 2026-10-18) | - |

## Dan to download

The one download list (2026-10-18; the earlier lists in OPEN-ITEMS and the research notes are folded in here). te.com,
littelfuse.com, eaton.com and glenair.com refuse shell downloads (TE 403, Littelfuse 403, Glenair 403, Eaton connection
reset / timeout, tested 2026-10-18), and agents no longer download through the in-app browser (it left Save dialogs open).
Save each file into the folder named, in this order (1 first):

| # | Part | Maker page URL | Save to | Why it is needed |
|---|---|---|---|---|
| 1 | TE customer drawing V23074-A2001-A402 (HEAD relays 5-1393292-8) | https://www.te.com/en/product-5-1393292-8.html ("Customer Drawing") | `te/specs/` | settles Needs Dan N24: drawing says 4 blades, TE 3D model shows a 5th (UNVERIFIED, R165) |
| 2 | TE Power Relay F4 A data sheet (V23136X0000A004), heater relay 1-1414687-0 | https://www.te.com/en/product-1-1414687-0.html ("Data Sheet") | `te/specs/` | confirm the heater relay pin pattern (today: the TE STEP + the Power Relay B numbers; OPEN-ITEMS row 132) |
| 3 | TE application spec 114-18022 | https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=114-18022&DocType=SS&DocLang=EN | `te/specs/` | MCP 2.8K crimp heights |
| 4 | TE application spec 114-20011 | https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=114-20011&DocType=SS&DocLang=EN | `te/specs/` | FASTON .187 crimp data (280919-2) |
| 5 | TE customer drawings DT04-4P-EP13, DT04-6P-EP13, DT04-08PA-P021, DT04-08PA-P026 (the 12-way DT04-12PA-P021 was read already) | https://www.te.com/en/product-DT04-4P-EP13.html, https://www.te.com/en/product-DT04-6P-EP13.html, https://www.te.com/en/product-DT04-08PA-P021.html, https://www.te.com/en/product-DT04-08PA-P026.html (each "Customer Drawing") | `te/specs/dt-bussed/` | only if Needs Dan N23 is not "none": bus layout per cavity and the 8-way pin / socket wording, which the TE page leaves unclear |
| 6 | TE DT application spec 114-151009 (46 pages) | https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=114-151009&DocType=Specification%20Or%20Standard&DocLang=English&DocFormat=pdf | `te/specs/dt-bussed/` | wire AWG 14-20 and the N-seal (2.23-3.68 mm) / E-seal (1.35-3.05 mm) insulation ranges, for any DT plug on thin M22759/16 wire |
| 7 | Glenair M22759/16 data sheet | https://www.glenair.com/wire-and-cable/as22759/pdf/m22759-16.pdf | `glenair/specs/` | finished wire outside diameter per gauge (the study used search-snippet values: about 1.5 / 1.8 / 2.0 / 2.4 mm for 20 / 18 / 16 / 14 AWG) |
| 8 | Littelfuse MINI 3D model (optional, to replace the built ATM) | https://info.littelfuse.com/ (MINI fuse 3D model form - fill it in yourself) | `littelfuse/MINI/` | an official mini fuse model |

The two 416-byte "Access Denied" pages saved as `te/specs/114-18022.pdf` / `114-20011.pdf` by an earlier session were deleted 2026-10-18.

## Dan to buy

Validated part numbers only (spec read on the maker's own TE page; dates 2026-10-18). Marketplace links are shopping leads: their
listing specs are not used, and "compatible" clones are not the TE part. No AliExpress listing was found for any of these.
Prices move; the Del City figures are single-piece prices seen that day.

| PN | What | Why | Where seen |
|---|---|---|---|
| 1-968851-1 | TE MCP 2.8 receptacle 16 / 14 AWG | LOGIC / ACPS mini fuse sockets (R166) | [Amazon, 3,500-piece reel](https://www.amazon.com/Connectivity-1-968851-1-3500-pcs-CONTACT/dp/B00HKI2Q6Q); eBay 30-piece lots (no single link kept) |
| 1-968849-1 | TE MCP 2.8 receptacle 20 / 18 AWG | same (R166) | none found on Amazon, AliExpress or eBay; buy from a TE distributor |
| DT04-12PA-P021 | DT 12-way bussed receptacle, 1 x 12 bus, 13 A per pin | only if Needs Dan N23 picks bussed splices (`sp_cp_sw12`; also the bulkhead A stars) | [Del City $19.53](https://www.delcity.net/store/wire-connectors-quick-splices/deutsch-connectors/dt-series/bussed-receptacles/12-way-one-pin-buss/); [eBay](https://www.ebay.com/itm/187450245478); [eBay, pair](https://www.ebay.com/itm/178136574903); [Amazon, no offers](https://www.amazon.com/DT04-12PA-P021-Terminals-Position-Contacts-Included/dp/B09JV82R4C) |
| DT04-08PA-P021 | DT 8-way bussed receptacle, 1 x 8 bus | N23: bulkhead A 5V and ground stars | [Del City $21.25, call for stock](https://www.delcity.net/store/wire-connectors-quick-splices/deutsch-connectors/dt-series/bussed-receptacles/8-way-one-pin-buss/); [eBay surplus](https://www.ebay.com/itm/354303361302) |
| DT04-6P-EP13 | DT 6-way bussed receptacle, black, 1 x 6 bus | N23: B-side and rear ground stars | [Del City $14.94](https://www.delcity.net/store/wire-connectors-quick-splices/deutsch-connectors/dt-series/bussed-receptacles/6-way-one-pin-buss/) |
| DT04-4P-EP13 | DT 4-way bussed receptacle, black, 1 x 4 bus | N23: small ground stars | [Del City $14.57](https://www.delcity.net/store/wire-connectors-quick-splices/deutsch-connectors/dt-series/bussed-receptacles/4-way-one-pin-buss/); [Amazon splice kit](https://www.amazon.com/Deutsch-DT-Enhanced-Splice-DT04-4P-EP13/dp/B06XKX5775); [eBay, 100 pcs](https://www.ebay.com/itm/186523927792) |
| DT06-12SA-CE05, DT06-08SA-CE05, DT06-6S-CE05, DT06-4S-CE05 | DT plugs with E-seal (1.35-3.05 mm wire) | N23: the plug half; the standard-seal DT06 Dan owns does not seal thin M22759/16 wire | TE pages only list them as "not currently available"; Amazon / eBay "DT06-12SA-CE05" listings exist (e.g. [eBay](https://www.ebay.com/itm/387064691560)) but may be clones: check the part number on the bag |

## Maker documents (data sheets, customer drawings)

| File | What |
|---|---|
| `littelfuse/specs/lf-mini32v.pdf` | Littelfuse MINI 297 series 32 V data sheet rev 09/27/2024 (dimensions page 2) |
| `littelfuse/specs/lf-mini-after.pdf` | Littelfuse MINI aftermarket data sheet |
| `littelfuse/specs/lf-mini-inline-holder.pdf` | Littelfuse 150 Mini in-line fuse holder (no terminal list) |
| `eaton/specs/eaton-skuPage.ATM-10.pdf` | Eaton ATM-10 spec sheet (no dimensions) |
| `eaton/specs/bus-ele-ds-2049-max.pdf` | Eaton MAX (MAXI) data sheet |
| `te/specs/te-cd-880398.pdf` | TE customer drawing 880398 rev L1 (fuse contact: 8.21 lance spread across the tines, box 5.4 x 3.9) |
| `te/specs/te-cd-444311.pdf`, `te-cd-444312.pdf`, `te-cd-444308.pdf` | TE 12-position fuse contact housings that TE lists as compatible with 880398-2 (444312 note 3: blade fuse per SAE J1284) |
| `te/specs/114-*.pdf` | TE application specs 114-2025, 114-2036, 114-20021, 114-35000 |
| `eaton/specs/bussmann-ami-series-p34.pdf` | Bussmann AMI series sheet p.34 (dimensions) |
