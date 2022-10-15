# Forked from https://github.com/seansivak/Disable_AP_Switchports_based_on_Tag
## Usage
### Interactive mode:
        docker run -ti fsedano/disable_ap_switchports_tag:latest

### Batch mode:
        docker run -e DNAC_SERVER=1.2.3.4 -e DNAC_USERNAME=user -e DNAC_PASSWORD=pass -e DNAC_VERIFICATION=preview -e DNAC_VERIFYDEPLOY=enabled -e DNAC_TAGNAME=tagname fsedano/disable_ap_switchports_tag:latest
