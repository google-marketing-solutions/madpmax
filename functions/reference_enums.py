# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module containing all data mappings.

Mad pMax works with a spreadsheet as data source, when changes are made to the
spreadsheet template, or sheetnames, they need to be updated here.
"""
import dataclasses
@dataclasses.dataclass(frozen=True)
class SheetNames:
    """A mapping of the sheetnames in input spreadsheet.

    Mad pMax relies on sheetnames to collect the input data, send it to the API
    and write status back to the sheet. This enum ensures a correct mapping to
    sheetnames, maintained from one single place.

    Atrributes:
      customers: Sheetname in spreadsheet containing customer details.
      campaigns: Sheetname in spreadsheet containing campaign details.
      new_campaigns: Sheetname in spreadsheet containing campaign input.
      asset_groups: Sheetname in spreadsheet containing asset group details.
      new_asset_groups: Sheetname in spreadsheet containing campaign input.
      sitelinks: Sheetname in spreadsheet containing sitelinks details and input.
      assets: Sheetname in spreadsheet containing assets details and input.
    """

    customers: str = "CustomerList"
    campaigns: str = "CampaignList"
    new_campaigns: str = "NewCampaigns"
    asset_groups: str = "AssetGroupList"
    new_asset_groups: str = "NewAssetGroups"
    sitelinks: str = "Sitelinks"
    assets: str = "Assets"


@dataclasses.dataclass(frozen=True)
class SheetRenges:
    """A mapping of the sheet ranges in input spreadsheet.

    Mad pMax relies on ranges on the sheet to collect the input data, send it to the API
    and write status back to the sheet. This enum ensures a correct column reference, maintained from one single place.

    Atrributes:
      customers: Range in spreadsheet containing customer details.
      campaigns: Range in spreadsheet containing campaign details.
      new_campaigns: Range in spreadsheet containing campaign input.
      asset_groups: Range in spreadsheet containing asset group details.
      new_asset_groups: Range in spreadsheet containing campaign input.
      sitelinks: Range in spreadsheet containing sitelinks details and input.
      assets: Range in spreadsheet containing assets details and input.
    """

    customers: str = "A6:B"
    campaigns: str = "A6:D"
    new_campaigns: str = "A6:L"
    asset_groups: str = "A6:F"
    new_asset_groups: str = "A6:T"
    sitelinks: str = "A6:J"
    assets: str = "A6:L"
