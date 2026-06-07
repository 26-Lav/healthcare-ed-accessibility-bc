# healthcare-ed-accessibility-bc
ML analysis of ED/UPCC accessibility in BC


# Healthcare ED Accessibility BC

Predicting ED/UPCC wait times and analyzing where the next ED Location should be 
across BC using ML, data engineering, and cloud platforms.

## Datasets
- Emergency Department (ED) / Urgent Primary Care Centre (UPCC) Wait Times (EDWaitTimes.csv)
- ED/UPCC Distances from BC Census Subdivisions (EDDistance/ )
- Canadian Census Data from BC (EDDistance/census_filtered.csv)
- Canadian Urban Environmental Health Research Consortium (CANUE) Data (CANUE Data/ )
- College of Physicians and Surgeons of BC (CPSBC) Data (CPSBC Family Physicians.csv)

## Emergency Department (ED) / Urgent Primary Care Centre (UPCC) Wait Time Data 

- Lists all EDs & UPCCs in the Vancouver Coastal Health and Fraser Health Authorities
- Indicates if the facility is open 24 hours per day or not
- Data are recorded in 1 hour intervals over a 5-month time period in 2025
- Each time point gives an estimated wait time in minutes

## Census and College of Physicians and Surgeons of BC Data 
- Canadian Census data are available from the last census (2021) for BC
- Available in the file EDDistance/census_filtered.csv
- Contains information on:
   - Population counts in 5-year age bins (e.g. 0-4 years, 5-9 years, etc.)
   - Number of private dwellings
   - Male:Female ratio
   - Number of dwellings by category (e.g. detached house, semi-detached house, row house, etc.)
   - Household size, marriage status, number of people/dwelling and more
- The number of family physicians who practice in each postal code has been compiled in the file CPSBC Family Physicians.csv

## Canadian Urban Environmental Health Research Consortium (CANUE) Data 
- Available via www.canuedata.ca
- Some data can be visualized at https://healthyplan.city/
- 100 environmental, social, economic and public health variables 
- Environmental data examples
   - Ozone, greenness, PM2.5 (particulate matter in air)
- Social data examples
   - Dwellings in need of repair, proximity to schools/grocery stores/places of employment/bus stops, material deprivation index
- Data dictionary available at CANUE Data/CANUE_data_dictionary
- Most data are annual measurements, but some monthly data
- All data localized to postal codes