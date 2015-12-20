#this file defines the user profile for different user type

#default profile
default_profile = {
    "Idle-Timeout":600,                     #600 second idle timeout
    "Session-Timeout":1800,                 #30 min session
    "WISPr-Bandwidth-Max-Up":1024,          #Uplink speed limit
    "WISPr-Bandwidth-Max-Down":4*1024,      #Down speed limit
}
#define profile for visitor
visitor_profile = {
    "Idle-Timeout":600,                     #600 second idle timeout
    "Session-Timeout":1800,                 #30 min session
    "WISPr-Bandwidth-Max-Up":1024,          #Uplink speed limit
    "WISPr-Bandwidth-Max-Down":4*1024,      #Down speed limit
}


#add visitor profile to user_profile dictionary for application usage
user_profiles['DEFAULT'] = default_profile
user_profiles['VISITOR'] = visitor_profile
