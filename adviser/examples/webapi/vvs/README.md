# Purpose

VVS API example shows you how to create a task-oriented dialogue system without a database as information source. Instead of looking up entities in a database, the information about departure and arrival time and information about a trip are dynamically extracted at runtime using the VVS API Wrapper.

# Files

`domain.py`: The code for the domain which performs the call to the vvs_api <br>
`nlu.py`: The code for the VVS-specific natural language understanding <br>
`bst.py`: The code for the adapted HandcraftedBST <br>
`nlg.py`: The code for the VVS-specific natural language generation <br>
`policy.py`:  File containing code for deciding which system acts to perform <br>
`vvs_api.py`: The code which requests the information via the VVS API Wrapper <br>
`data`: folder containing csv file for the VVS API containing information about the stations