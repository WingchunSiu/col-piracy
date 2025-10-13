Platform API Reference
Endpoints
The Dailymotion Platform API is served over HTTPS and accessible on the following endpoints depending on your API key type:

Public API key
Private API key
https://api.dailymotion.com
We recommend using UTF-8 encoding for all interactions with the API.

Getting started
To get more insights before diving into the API reference, please read the Getting started article to see how to authenticate and interact with the API objects, fields and filters.

Global API Parameters
The following query-string parameters are valid for all API objects and can be provided along with any type of request. Some of them are strongly recommended if you want to enhance your end-user experience.

Parameter	Description	Type
ams_country	Change the country for the asset management.
By default, the country is auto-detected based on the IP address of the API consumer. Changing this value will filter out content geo-blocked for the defined country and will affect the geo-blocking mechanism.	string
context	Additional call context for this request.
Some resources of the API require that you provide contextual information along with your request in order to return relevant data. This is especially useful when the API cannot retrieve or guess this additional information by itself. Contextual information should only be provided when expressly needed by the resource you are trying to query. Values should be passed as an embedded and URL encoded query string.

E.g.: ?field=data&context=key1%3Dvalue1%26key2%3Dvalue2
string
device_filter	Filter out content and change media assets.
By default, the device is auto-detected based on the user-agent of the API consumer. Changing this value will filter out content not allowed on the defined device.

Possible values: detect web mobile and iptv	string
family_filter	Enable/disable the “sensitive content” filter.
By default, the family filter is turned on. Setting this parameter to false will stop filtering-out explicit content from searches and global contexts. You should always check the result’s explicit field when applicable as some contexts may still return those contents. You should also flag them in your UI to warn the user about the nature of the content.

Possible: true or false	boolean
localization	Change the default localization of the user.
This will affect results language and content selection. Note that changing the localization won’t give access to geoblocked content of the corresponding location. The IP address of the API consumer is always used for this kind of restriction.

You can use a standard locale like fr_FR, en_US (or simply en, it) but you can also provide detect to tell the API to detect the most probable locale based on the consumer’s location	string
thumbnail_ratio	Change the size ratio for all video thumbnails.

By default: original
Possible values: original, widescreen and square	string
To use a global parameter, simply add it to any request’s query-string like so:

GET https://api.dailymotion.com/video?family_filter=false&localization=it
Auth
This endpoint enables to access information about the current authenticated user. This relates to the user authenticated using an access token (provided with the appropriate header or as a query-string parameter).

Retrieving current auth information
To retrieve information about the current authenticated user, perform a GET request on /auth. By default, only a small number of default fields are returned, please refer to the complete field list below.

Sample auth API call: /auth

Current auth information response
Here is the list of fields you can retrieve when performing a call on /auth.

Field name	Description	Sample
id	The user identifier of the authenticated user.	"x1fz4ii"
scope	The scope of permissions granted to the authenticated user.	["manage_videos","userinfo"]
roles	The list of roles associated to the API key of the authenticated user.	[]
username	The username of the authenticated user.	"DailymotionAPI"
screenname	The authenticated user’s username or full name depending on his preferences.	"Dailymotion API"
language	The authenticated user spoken language (declarative).	"fr"
Channel
Channel
A channel object represents a category of videos on Dailymotion (formerly a channel), for example: shortfilms, videogames, news, etc. (See full list below)

Manipulating channels
To retrieve a specific channel object, perform a GET request on /channel/<CHANNEL_ID>. By default, only a small number of fields marked as default are returned (such as the object identifier), please refer to the complete field list below. For help on requesting specific fields, see the fields selection section.

To retrieve a list of channel objects, perform a GET request on /channels. You can then use filters (if any) to filter down the result set, see the filtering section for more information.

Sample channel API call: 
/channel/music

Test it further with the API Explorer.

Channel fields
Here is the list of fields you can retrieve on every channel object. You can retrieve these using the fields query-string parameter on any graph object request. See the fields selection section for more information.

Expand all
Collapse all
DATE
created_time
Date and time when this channel was created.

STRING
description
Comprehensive localized description of this channel.

IDENTIFIER
id
Unique object identifier (unique among all channels)

STRING
item_type
Graph type of this object (hopefully channel)

STRING
name
Localized short name of this channel.

STRING
slug
Slug name of this channel.

DATE
updated_time
Date and time when this channel was last updated.

Channel filters
Here is the list of filters you can use to limit a result set of channel objects. You can use these by passing them as query-string parameters with your request.

Expand all
Collapse all
sort
Change the default result set ordering.

Channel deprecated filters
These deprecated filters were once part of the API reference but are no longer maintained. Support is still available until the end of life date specified for each filter. Do not use any of these for a new project as they may disappear without warning.

Expand all
Collapse all
 language
Language in which you want this channel name and description fields to be.

Channel connections
Connections through the data API are used to link objects with each others. Some objects can only be accessed and/or created through connections since they have no point in existing on their own. Here is the list of connections available through the channel object.

Expand all
Collapse all
[User]
users
List of the top users of this channel.
This connection joins an object of type channel with a list of user objects.

[Video]
videos
List of videos of this channel.
This connection joins an object of type channel with a list of video objects.

List of categories
The full list of available categories (channel object) is as follow:

CATEGORY	NAME
animals	Animals
creation	Creative
auto	Cars
school	Education
people	Celeb
fun	Comedy & Entertainment
videogames	Gaming
tech	Tech
kids	Kids
lifestyle	Lifestyle & How-To
shortfilms	Movies
music	Music
news	News
sport	Sport
tv	TV
travel	Travel
webcam	Webcam
Note: Choosing a category is mandatory when uploading a video on Dailymotion
Echo
This endpoint returns the same exact message which was given as a parameter. It can be used to test the availability and reactivity of the API.

Using echo
To send an /echo request, perform a GET request on /echo. The table below lists all the parameters that can be provided when performing this request:

Type	Parameter	Required	Description
string	message		The message to be returned by the echo.
Sample echo API call: /echo?message=this+is+a+test

Echo response
Here is the list of fields you can retrieve when performing a call on /echo.

Field name	Description	Sample
message	The message which was given as a parameter.	"echo... echo... echo..."
File
This endpoint allows anyone to retrieve a video upload URL, when you need to upload a video on Dailymotion’s servers and don’t want to upload it on your own server.

File upload
To retrieve an upload URL, perform a GET request on /file/upload.

Sample file upload API call: https://api.dailymotion.com/file/upload

File upload response
Here is the list of fields you can retrieve when performing a call on /file/upload.

Field name	Description	Sample
upload_url	The URL you will be able to upload your video to.	http://upload-XX.dailymotion.com/upload?uuid=<UUID>&seal=<SEAL>
progress_url	An URL to poll the progress of the current upload. A GET request to this URL returns a JSON object with a state key having one of the following values: starting, uploading, done, error. During the uploading state, the JSON object also contains size and received keys reporting the upload progress.	http://upload-XX.dailymotion.com/progress?uuid=<UUID>
Note:

The upload process requires a minimum version of TLS 1.2 protocol
Languages
The languages endpoint is used to retrieve the list of ISO-639-3 2 or 3 letter codes associated with the language name, native name, localized name, and name as it could be displayed on Dailymotion.

Retrieving languages
To retrieve the list of ISO-639-3 languages, perform a GET request on /languages.

The list of fields returned is fixed and defined as followed. This call do not support the fields parameter.

Sample locale API call: /languages

Languages response
Here is the list of fields you will retrieve when performing a call on /languages.

Field name	Description	Sample
code	The language alpha-2 or alpha-3 code as specified by the ISO-639-3 standard.	"ja"
name	The name of the language.	"Japanese"
native_name	The native name of the language, or null if unknown.	"日本語"
localized_name	The name of the language in the locale of the request, or null if unknown.	"Japonais"
display_name	The name of the language as it could be displayed. This corresponds to the localized name if we know it, otherwise it’s simply the name.	"Japonais"
Locale
A locale is a set of parameters that defines a user’s language, country, currency, etc.

Detecting and retrieving locales
To detect the locale of the current requestor, perform a GET request on /locale.

To retrieve the list of locales supported by Dailymotion, perform a GET request on /locales.

In both cases, the list of fields returned is fixed and defined as follow since these calls do not support the fields parameter. You can also return informations on a specific locale by changing your request locale using the localization global parameter.

Sample locale API call: /locale

Locale detection response
Here is the list of fields you will retrieve when performing a call on /locale or /locales.

Field name	Description	Sample
locale	The locale code.	"ja_JP"
site_code	The site version code associated to the locale. This code is to be used in the API wherever a “localization” parameter is requested	"jp"
language	The name of the language in English.	"Japanese"
localized_language	The name of the language in the current API request locale.	"Japonais"
locally_localized_language	The name of the language in the locale’s language.	"日本語"
country	The name of the country in English	"Japan"
localized_country	The name of the country in the current API request locale.	"Japon"
locally_localized_country	The name of the country in the locale’s language.	"日本"
currency	The currency accepted by Dailymotion for this locale.	"JPY"
Logout
This endpoint removes the right for the current API key to access the current user account (the user authenticated by the current access token). Once this method is called, all further requests with the same access token will fail and any previously obtained refresh token for this session will be invalidated.

Logging out
To logout a user, perform a GET request on /logout. This call returns an empty JSON object in case of success: {}

Sample logout API call: /logout

Player
Player
A player object holds several configuration properties (Picture In Picture settings, aspect ratio…) and is meant to be embedded on a webpage with a script tag.

Manipulating players
To retrieve a specific player object, perform a GET request on /player/<PLAYER_ID>. By default, only a small number of fields marked as default are returned (such as the object identifier), please refer to the complete field list below. For help on requesting specific fields, see the fields selection section.

To create an object of type player, perform a POST request on the connection available through the user graph object. Join all the fields you want to specify and their value as an application/x-www-form-urlencoded payload. Please note that, for creation, some fields and/or specific query-string parameters could be mandatory, please refer to the field list below.

To edit an object of type player, perform a POST request on /player/<PLAYER_ID>. Join all the fields you want to update and their new value as an application/x-www-form-urlencoded payload.

To delete an object of type player, perform a DELETE request on /player/<PLAYER_ID>. If you do not receive any error (empty result set), it means that the deletion was successful.

Sample player API call: 
/player/xid1

Test it further with the API Explorer.

Player fields
Here is the list of fields you can retrieve on every player object. You can retrieve these using the fields query-string parameter on any graph object request. See the fields selection section for more information.

Expand all
Collapse all
STRING
aspect_ratio
To specify the aspect ratio of the player

NUMBER
autoskip_after
After how many seconds the video is skipped (min: 10)

STRING
autostart
To control how the player handles autoplay

STRING
color
Change the default highlight color used in the controls

NUMBER
contextual_content_freshness
Define the freshness of the content (in days) that can be selected by the contextual embed feature

STRING
contextual_content_source
Define if your contextual content should be taken from your organization, your channel or Dailymotion’s global catalog

DATE
created_time
Date and time when this player was created

URL
embed_html_url
URL of the player HTML embed

URL
embed_script_url
URL of the player to be used in a script HTML tag

BOOLEAN
enable_ads
Whether to enable ads and associated tracking

BOOLEAN
enable_ads_controls
Whether to display the player controls during an ad

BOOLEAN
enable_attention_peaks
Whether to display attention peaks above seekbar

BOOLEAN
enable_automatic_recommendations
Whether to enable automatic recommendations

BOOLEAN
enable_autonext
Whether to automatically play the next video item

BOOLEAN
enable_autoskip
Whether to activate the "Auto skip" feature

BOOLEAN
enable_channel_link
Whether to activate the link on the channel owner text

BOOLEAN
enable_click_to_unmute
Whether to enable the click to unmute feature

BOOLEAN
enable_contextual_content
Whether to load relevant content based on contextual information from the embedder page

BOOLEAN
enable_contextual_content_fallback
Whether to allow the contextual embed feature to play less relevant videos from your channel or other sources, to avoid displaying an empty player when content with high relevancy is not available

BOOLEAN
enable_contextual_content_freshness
Whether to activate the "Contextual content freshness" feature

BOOLEAN
enable_custom_recommendations
Whether to enable custom recommendations

BOOLEAN
enable_dm_logo
Whether to display the Dailymotion logo

BOOLEAN
enable_eco_mode
Whether to enable Eco Mode to apply a quality limit

BOOLEAN
enable_google_policy_ui
Whether to activate the UI to be Google policy compliant (e.g.: PIP close button outside Player UI)

BOOLEAN
enable_info
Whether to display the video title and owner information

BOOLEAN
enable_keyboard_shortcuts
Whether to enable the keyboard shortcuts

BOOLEAN
enable_legacy_pip
When enabled, player displays the legacy PiP version

BOOLEAN
enable_live_offair_screen
Whether to display streaming status before and after live streaming

BOOLEAN
enable_paid_partnership_label
Whether to enable the paid partnership label (if the playing video is flagged as such)

BOOLEAN
enable_pip_placement
Whether to choose the webpage corner where PiP is initialized. If used, overwrites PiP CSS customization

BOOLEAN
enable_playback_controls
Whether to display the player controls during a video

BOOLEAN
enable_receive_url_location
Allow player to receive full page URL where player is embedded

BOOLEAN
enable_sharing
Whether to enable the sharing button

BOOLEAN
enable_sharing_url_location
Whether to share the location where the video is embedded (video URL by default)

BOOLEAN
enable_spinner
Whether to display spinner during video loading

BOOLEAN
enable_start_pip_expanded
Whether to start PiP in expanded mode on mobile (if legacy PiP is enabled)

BOOLEAN
enable_startscreen_dm_link
Whether to show the "Watch on Dailymotion" link on the startscreen

BOOLEAN
enable_subtitles
Whether to activate the subtitles in the player

BOOLEAN
enable_tap_to_unmute
Whether to enable the tap to unmute feature

BOOLEAN
enable_titles_in_video_cards
Whether to show the videos titles in the carousel on the endscreen

BOOLEAN
enable_video_title_link
Whether to activate the link on the video title text

BOOLEAN
enable_wait_for_custom_config
Whether to configure the player to wait for the custom config object before starting playback

BOOLEAN
enable_watch_now_card
Whether to display one video card after playback

BOOLEAN
has_reached_playback_limits
Whether the organization that owns the player has reached some limits (bandwidth, plays)

BOOLEAN
has_recommendations_from_org_only
Whether the organization that owns the player includes only videos from this organization in recommendations

BOOLEAN
has_ssai
Whether the organization that owns the player has SSAI enabled

IDENTIFIER
id
Unique object identifier (unique among all players)

STRING
item_type
Graph type of this object (hopefully player)

STRING
label
Mandatory player label

URL
lib_script_url
URL of the player embed library to be used in a script HTML tag

User
owner
Owner of this player. You can retrieve sub-fields of this user object using the dot-notation (e.g.: owner.id).

STRING
pip
Picture-in-Picture mode

STRING
pip_selected_placement
Define the webpage corner where PiP is initialized

STRING
recommendations_optimisation
Optimise recommendations based on selected model: monetization, engagement, views

DATE
updated_time
Date and time when this player was updated

NUMBER
wait_for_custom_config_delay
How long to wait before the ad request is made (min: 1s – max: 10s), when enable_wait_for_custom_config is enabled

STRING
watermark_image_type
Image type of the watermark

STRING
watermark_link_type
Type of watermark link

URL
watermark_link_url
URL of the watermark link

Player deprecated fields
These deprecated fields were once part of the API reference but are no longer maintained. Support is still available until the end of life date specified for each field. Do not use any of these for a new project as they may disappear without warning.

Expand all
Collapse all
BOOLEAN
 enable_controls
Whether to display the player controls

BOOLEAN
 enable_queue
Whether to enable automatic recommendations

Player filters
Here is the list of filters you can use to limit a result set of player objects. You can use these by passing them as query-string parameters with your request.

Expand all
Collapse all
search
Limit the result set to this full text search.

Playlist
Playlist
A playlist object represents an ordered list of videos created by a user. Videos in a playlist do not necessarily have anything in common.

Manipulating playlists
To retrieve a specific playlist object, perform a GET request on /playlist/<PLAYLIST_ID>. By default, only a small number of fields marked as default are returned (such as the object identifier), please refer to the complete field list below. For help on requesting specific fields, see the fields selection section.

To retrieve a list of playlist objects, perform a GET request on /playlists. You can then use filters (if any) to filter down the result set, see the filtering section for more information.

To create an object of type playlist, perform a POST request on Join all the fields you want to specify and their value as an application/x-www-form-urlencoded payload. Please note that, for creation, some fields and/or specific query-string parameters could be mandatory, please refer to the field list below.

To edit an object of type playlist, perform a POST request on /playlist/<PLAYLIST_ID>. Join all the fields you want to update and their new value as an application/x-www-form-urlencoded payload.

To delete an object of type playlist, perform a DELETE request on /playlist/<PLAYLIST_ID>. If you do not receive any error (empty result set), it means that the deletion was successful.

Sample playlist API call: 
/playlist/x3ecgj

Test it further with the API Explorer.

Playlist fields
Here is the list of fields you can retrieve on every playlist object. You can retrieve these using the fields query-string parameter on any graph object request. See the fields selection section for more information.

Expand all
Collapse all
DATE
created_time
Date and time when this playlist was created.

STRING
description
Comprehensive description of this playlist.

IDENTIFIER
id
Unique object identifier (unique among all playlists)

STRING
item_type
Graph type of this object (hopefully playlist)

STRING
name
Short descriptive name of this playlist.

User
owner
Author of this playlist. You can retrieve sub-fields of this user object using the dot-notation (e.g.: owner.id).

BOOLEAN
private
True if this playlist is private.

URL
thumbnail_60_url
URL of this playlist’s first video thumbnail image (60px height).

URL
thumbnail_120_url
URL of this playlist’s first video’s thumbnail image (120px height).

URL
thumbnail_180_url
URL of this playlist’s first video’s thumbnail image (180px height).

URL
thumbnail_240_url
URL of this playlist’s first video’s thumbnail image (240px height).

URL
thumbnail_360_url
URL of this playlist’s first video’s thumbnail image (360px height).

URL
thumbnail_480_url
URL of this playlist’s first video’s thumbnail image (480px height).

URL
thumbnail_720_url
URL of this playlist’s first video’s thumbnail image (720px height).

URL
thumbnail_1080_url
URL of this playlist’s first video’s thumbnail image (1080px height).

URL
thumbnail_url
URL of the thumbnail of this playlist’s first video (raw, respecting full size ratio).

DATE
updated_time
Date and time when this playlist was last updated.

NUMBER
videos_total
Total amount of videos in this playlist.

Playlist deprecated fields
These deprecated fields were once part of the API reference but are no longer maintained. Support is still available until the end of life date specified for each field. Do not use any of these for a new project as they may disappear without warning.

Expand all
Collapse all
STRING
 relative_updated_time
Localized date and time when this playlist was last updated (formatted).

URL
 thumbnail_large_url
URL of the thumbnail of this playlist’s first video (320px by 240px).

URL
 thumbnail_medium_url
URL of the thumbnail of this playlist’s first video (160px by 120px).

URL
 thumbnail_small_url
URL of the thumbnail of this playlist’s first video (80px by 60px).

Playlist filters
Here is the list of filters you can use to limit a result set of playlist objects. You can use these by passing them as query-string parameters with your request.

Expand all
Collapse all
ids
Limit the result set to this list of playlist identifiers (works only with xids).

owner
Limit the result set to playlists of this user.

private
Limit the result set to private playlists

search
Limit the result set to this full text search.

sort
Change the default result set ordering.

verified
Limit the result set to verified partner playlists.

Playlist connections
Connections through the data API are used to link objects with each others. Some objects can only be accessed and/or created through connections since they have no point in existing on their own. Here is the list of connections available through the playlist object.

Expand all
Collapse all
[Video]
videos
List of videos contained in this playlist (in the order defined by its owner).
This connection joins an object of type playlist with a list of video objects.

Subtitles
Subtitle
A subtitle object represents a file resource containing closed captioning for a given video.

Manipulating subtitles
To retrieve a specific subtitle object, perform a GET request on /subtitle/<SUBTITLE_ID>. By default, only a small number of fields marked as default are returned (such as the object identifier), please refer to the complete field list below. For help on requesting specific fields, see the fields selection section.

To create an object of type subtitle, perform a POST request on the connection available through the video graph object. Join all the fields you want to specify and their value as an application/x-www-form-urlencoded payload. Please note that, for creation, some fields and/or specific query-string parameters could be mandatory, please refer to the field list below.

Type	Parameter	Required	Description
STRING	
format
No	
Data format SRT only is supported, if you have an other format please convert it to SRT.

STRING	
language
No	
Language of these subtitles.

URL	
url
No	
On GET, the URL pointing to the latest version of the subtitles. On POST, URL pointing to the subtitle data in on of the valid formats. You don’t need to host the file, you can use the GET /file/upload API ressource to create a temporary URL to a file of your own, just like when you upload a video source file. If you host your own file, the file will be fetched and the subtitles URL will point to a local copy.

To delete an object of type subtitle, perform a DELETE request on /subtitle/<SUBTITLE_ID>. If you do not receive any error (empty result set), it means that the deletion was successful.

Sample subtitle API call: 
/video/x26m1j4/subtitles

Test it further with the API Explorer.

Subtitle fields
Here is the list of fields you can retrieve on every subtitle object. You can retrieve these using the fields query-string parameter on any graph object request. See the fields selection section for more information.

Expand all
Collapse all
STRING
format
Data format SRT only is supported, if you have an other format please convert it to SRT.

IDENTIFIER
id
Unique object identifier (unique among all subtitles)

STRING
item_type
Graph type of this object (hopefully subtitle)

STRING
language
Language of these subtitles.

STRING
language_label
Subtitles’s language in its own language.

URL
url
On GET, the URL pointing to the latest version of the subtitles. On POST, URL pointing to the subtitle data in on of the valid formats. You don’t need to host the file, you can use the GET /file/upload API ressource to create a temporary URL to a file of your own, just like when you upload a video source file. If you host your own file, the file will be fetched and the subtitles URL will point to a local copy.

Subtitle filters
Here is the list of filters you can use to limit a result set of subtitle objects. You can use these by passing them as query-string parameters with your request.

Expand all
Collapse all
language
Limit the result set to subtitles of this language.

User
User
A user object represents a Dailymotion user account. Users are at the foundation of every other graph objects, since most of them are created through —or owned by— users. Users also represent the main authentication vector to Dailymotion services.

Manipulating users
To retrieve a specific user object, perform a GET request on /user/<USER_ID>. By default, only a small number of fields marked as default are returned (such as the object identifier), please refer to the complete field list below. For help on requesting specific fields, see the fields selection section.

To retrieve a list of user objects, perform a GET request on /users. You can also use one of the several connections available through the channel and user graph objects. You can then use filters (if any) to filter down the result set, see the filtering section for more information.

To edit an object of type user, perform a POST request on /user/<USER_ID>. Join all the fields you want to update and their new value as an application/x-www-form-urlencoded payload.

To delete an object of type user, perform a DELETE request on /user/<USER_ID>. If you do not receive any error (empty result set), it means that the deletion was successful.

Sample user API call: 
/user/x1fz4ii

Test it further with the API Explorer.

User fields
Here is the list of fields you can retrieve on every user object. You can retrieve these using the fields query-string parameter on any graph object request. See the fields selection section for more information.

Expand all
Collapse all
STRING
active
Force user account active.

STRING
address
Postal address of this user.

BOOLEAN
advanced_statistics
advanced-statistics criteria of this user.

URL
avatar_25_url
URL of this user’s avatar image (25px wide square).

URL
avatar_60_url
URL of this user’s avatar image (60px wide square).

URL
avatar_80_url
URL of this user’s avatar image (80px wide square).

URL
avatar_120_url
URL of this user’s avatar image (120px wide square).

URL
avatar_190_url
URL of this user’s avatar image (190px wide square).

URL
avatar_240_url
URL of this user’s avatar image (240px wide square).

URL
avatar_360_url
URL of this user’s avatar image (360px wide square).

URL
avatar_480_url
URL of this user’s avatar image (480px wide square).

URL
avatar_720_url
URL of this user’s avatar image (720px wide square).

URL
avatar_url
URL of an image to change this user’s avatar.

BOOLEAN
ban_from_partner_program
True if this user has the criteria ban-from-partner-program.

DATE
birthday
Birthday date of this user.

NUMBER
children_total
Total number of user children.

STRING
city
City of residence of this user.

STRING
country
Country of residence of this user. Allowed values are ISO 3166-1 alpha-2 country codes.

URL
cover_100_url
URL of this user’s cover image (height = 100px).

URL
cover_150_url
URL of this user’s cover image (height = 150px).

URL
cover_200_url
URL of this user’s cover image (height = 200px).

URL
cover_250_url
URL of this user’s cover image (height = 250px).

URL
cover_url
URL of this user’s cover image (original size).

DATE
created_time
Date and time when this user joined the site.

STRING
description
Comprehensive description of this user.

EMAIL
email
Email address of this user.

STRING
facebook_url
Facebook profile URL of this user.

STRING
first_name
First name of this user.

NUMBER
followers_total
Total amount of followers of this user.

NUMBER
following_total
Total amount of users this user is following.

STRING
fullname
Full name of this user.

STRING
gender
Gender of this user.

STRING
googleplus_url
Googleplus profile URL of this user.

IDENTIFIER
id
Unique object identifier (unique among all users)

STRING
instagram_url
Instagram profile URL of this user.

BOOLEAN
is_following
True if the authenticated user is following this user. If no user is authenticated, it will always return false

STRING
item_type
Graph type of this object (hopefully user)

STRING
language
Language used by this user. Allowed values are ISO-639-3 alpha-2 and alpha-3 language codes.

STRING
last_name
Last name of this user.

DICT
limits
Returns the various user limits like the maximum allowed duration and size per uploaded video etc. This property can only be obtained for the currently logged in user.

STRING
linkedin_url
LinkedIn profile URL of this user.

User
parent
Identifier of this user’s parent (use parent.screenname to access its user name). You can retrieve sub-fields of this user object using the dot-notation (e.g.: parent.id).

BOOLEAN
partner
When the partner field is set, the user auto-accepts the T&Cs (https://www.dailymotion.com/legal/partner) and becomes a partner. Returns True if this user is a partner.

STRING
pinterest_url
Pinterest profile URL of this user.

NUMBER
playlists_total
Total amount of playlists of this user.

NUMBER
reposts_total
The number of videos reposted by the user.

NUMBER
revenues_claim_last_day
Total amount of net revenues in USD generated through claim the last day.

NUMBER
revenues_claim_last_month
Total amount of net revenues in USD generated through claim the last month.

NUMBER
revenues_claim_last_week
Total amount of net revenues in USD generated through claim in the last 7 sliding days.

NUMBER
revenues_claim_total
Total amount of net revenues in USD generated through claim since the beginning.

NUMBER
revenues_paidcontent_last_day
Total amount of net revenues in USD generated through the paid content the last day.

NUMBER
revenues_paidcontent_last_month
Total amount of net revenues in USD generated through the paid content the last month.

NUMBER
revenues_paidcontent_last_week
Total amount of net revenues in USD generated through the paid content in the last 7 sliding days.

NUMBER
revenues_paidcontent_total
Total amount of net revenues in USD generated through the paid content since the beginning.

NUMBER
revenues_video_last_day
Total amount of net revenues in USD generated through the video monetization the last day.

NUMBER
revenues_video_last_month
Total amount of net revenues in USD generated through the video monetization the last month.

NUMBER
revenues_video_last_week
Total amount of net revenues in USD generated through the video monetization in the last 7 sliding days.

NUMBER
revenues_video_total
Total amount of net revenues in USD generated through the video monetization since the beginning.

NUMBER
revenues_website_last_day
Total amount of net revenues in USD generated through the website monetization the last day.

NUMBER
revenues_website_last_month
Total amount of net revenues in USD generated through the website monetization the last month.

NUMBER
revenues_website_last_week
Total amount of net revenues in USD generated through the website monetization in the last 7 sliding days.

NUMBER
revenues_website_total
Total amount of net revenues in USD generated through the website monetization since the beginning.

STRING
screenname
Returns this user’s full name or login depending on the user’s preferences.

STRING
status
Current user account status.

STRING
twitter_url
Twitter profile URL of this user.

URL
url
URL of this user’s profile on Dailymotion.

STRING
username
User account credentials login.

BOOLEAN
username_update_required
True if this user needs to update his username, False otherwise.

BOOLEAN
verified
True if this user is a verified partner.

NUMBER
videos_total
Total amount of public videos of this user.

NUMBER
views_total
Total aggregated number of views on all of this user’s videos.

STRING
website_url
Personal website URL of this user.

User deprecated fields
These deprecated fields were once part of the API reference but are no longer maintained. Support is still available until the end of life date specified for each field. Do not use any of these for a new project as they may disappear without warning.

Expand all
Collapse all
COMPLEX
 analytics_services
Analytics service of this user.

URL
 avatar_large_url
URL of this user’s avatar image (160px wide square).

URL
 avatar_medium_url
URL of this user’s avatar image (80px wide square).

URL
 avatar_small_url
URL of this user’s avatar image (40px wide square).

URL
 background_url
URL of this user’s background image (Max 1680px by 2000px).

URL
 banner_url
URL of this user’s banner image (Max 970px by 120px).

NUMBER
 fans_total
Total amount of fans of this user.

BOOLEAN
 live_notification_followed_onair
True if this user has authorized live notifications, false otherwise.

STRING
 type
Type of user account.

Video
 videostar
Showcased video of this user. You can retrieve sub-fields of this video object using the dot-notation (e.g.: videostar.id).

User filters
Here is the list of filters you can use to limit a result set of user objects. You can use these by passing them as query-string parameters with your request.

Expand all
Collapse all
country
Country of residence of this user. Allowed values are ISO 3166-1 alpha-2 country codes.

exclude_ids
List of user ids to exclude from the result set.

flags
List of simple boolean flags available to reduce the result set.

ids
Limit the result set to this list of user channels identifiers.

language
Limit the result set to users using this language.

mostpopular
Limit the result set to the most popular users.

parent
Limit the result set to children of this user.

partner
Limit the result set to partner users.

recommended
Limit the result set to recommended users.

recommendedforchannel
Limit the result set to this channel’s top users.

sort
Change the default result set ordering. Notes:

Deprecated sorts (recent, daily, weekly, monthly, rated, random, alpha, alphaZA, alphaZAFullname)
usernames
Limit the results set to users with a list of usernames

verified
Limit the result set to verified partner users.

User deprecated filters
These deprecated filters were once part of the API reference but are no longer maintained. Support is still available until the end of life date specified for each filter. Do not use any of these for a new project as they may disappear without warning.

Expand all
Collapse all
 filters
List of simple boolean filters available to reduce the result set.

 list
Limit the result set to this user list.

 search
Limit the result set to this full text search.

User connections
Connections through the data API are used to link objects with each others. Some objects can only be accessed and/or created through connections since they have no point in existing on their own. Here is the list of connections available through the user object.

Expand all
Collapse all
[User]
children
List of this user’s children.
This connection joins an object of type user with a list of user objects.

[Video]
features
List of videos featured by this user.
This connection joins an object of type user with a list of video objects.

[User]
followers
List of this user’s followers.
This connection joins an object of type user with a list of user objects.

[User]
following
List of users followed by this user.
This connection joins an object of type user with a list of user objects.

[Video]
likes
List of videos liked by the user.
This connection joins an object of type user with a list of video objects.

[User]
parents
List of this user’s parents.
This connection joins an object of type user with a list of user objects.

[Player]
players
List of players created by this user
This connection joins an object of type user with a list of player objects.

[User]
relations
List of user accounts related to this user through their parents.
This connection joins an object of type user with a list of user objects.

[Video]
subscriptions
List of videos from the channels the user follow.
This connection joins an object of type user with a list of video objects.

[Video]
videos
List of videos uploaded by this user.
This connection joins an object of type user with a list of video objects.

[Video]
watchlater
List of watch later videos.
This connection joins an object of type user with a list of video objects.

User deprecated connections
These deprecated connections were once part of the API reference but are no longer maintained. Support is still available until the end of life date specified for each filter. Do not use any of these for a new project as they may disappear without warning.

Expand all
Collapse all
[Video]
 favorites
List of videos favorited by this user.
This connection joins an object of type user with a list of video objects.

[User]
 recommended
List of users recommended to this user.
This connection joins an object of type user with a list of user objects.

Video
Video
The video object is the foundation of Dailymotion’ service. Videos are metadata containers wrapped around media streams and can be accessed either directly or through several connections through the Data API.

Manipulating videos
To retrieve a specific video object, perform a GET request on /video/<VIDEO_ID>. By default, only a small number of fields marked as default are returned (such as the object identifier), please refer to the complete field list below. For help on requesting specific fields, see the fields selection section.

To retrieve a list of video objects, perform a GET request on /videos. You can also use one of the several connections available through the channel, playlist, user and video graph objects. You can then use filters (if any) to filter down the result set, see the filtering section for more information.

To create an object of type video, perform a POST request on the connection available through the user graph object. Join all the fields you want to specify and their value as an application/x-www-form-urlencoded payload. Please note that, for creation, some fields and/or specific query-string parameters could be mandatory, please refer to the field list below.

Type	Parameter	Required	Description
STRING	
content_provider
No	
Content provider name.

To edit an object of type video, perform a POST request on /video/<VIDEO_ID>. Join all the fields you want to update and their new value as an application/x-www-form-urlencoded payload.

To delete an object of type video, perform a DELETE request on /video/<VIDEO_ID>. If you do not receive any error (empty result set), it means that the deletion was successful.

Sample video API call: 
/video/x26m1j4

Test it further with the API Explorer.

Video fields
Here is the list of fields you can retrieve on every video object. You can retrieve these using the fields query-string parameter on any graph object request. See the fields selection section for more information.

Expand all
Collapse all
STRING
advertising_custom_target
Returns the custom target value for

given video. This value is sent to Liverail as an LR_DM_ADPARAM param. This can be used for targeting in liverail.

BOOLEAN
advertising_instream_blocked
True if the owner blocked instream ads on this video.

BOOLEAN
ai_chapter_generation_required
Whether AI chapter generation is required for the video or not.

BOOLEAN
allow_embed
True if this video can be embedded outside of Dailymotion.

BOOLEAN
allowed_in_playlists
True if this video can be added to playlists.

NUMBER
aspect_ratio
Aspect ratio of this video (i.e.: 1.33333 for 4/3, 1.77777 for 16/9…).

NUMBER
audience
Current live stream audience. null if the audience shouldn’t be taken into consideration.

NUMBER
audience_total
Total live stream audience since stream creation. null if the audience shouldn’t be taken into account.

URL
audience_url
Audience meter URL to be used for this video. null if the audience shouldn’t be taken into account.

ARRAY
available_formats
List of available stream formats for this video.

Channel
channel
Channel of this video. You can retrieve sub-fields of this channel object using the dot-notation (e.g.: channel.id).

STRING
checksum
Video file hash.

ARRAY
claim_rule_blocked_countries
List of countries where this video is blocked by the claimer. A list of country codes (ISO 3166-1 alpha-2) e.g.: ["FR", "US"] will block this video in France and US.

ARRAY
claim_rule_monetized_countries
List of countries where this video is monetized by the claimer. A list of country codes (ISO 3166-1 alpha-2) e.g.: ["FR", "US"] will monetize this video in France and US.

ARRAY
claim_rule_tracked_countries
List of countries where this video is tracked by the claimer. A list of country codes (ISO 3166-1 alpha-2) e.g.: ["FR", "US"] will track this video in France and US but it won’t be blocked nor monetized by the claimer.

STRING
content_provider
Content provider name.

STRING
content_provider_id
Content provider identifier.

STRING
country
Country of this video (declarative, may be null). Allowed values are ISO 3166-1 alpha-2 country codes.

DATE
created_time
Date and time when this video was uploaded.

ARRAY
custom_classification
List of customizable values (maximum of 3 values)

STRING
description
Comprehensive description of this video. Maximumm length is set to 3000 (5000 for partners).

NUMBER
duration
Duration of this video in seconds.

STRING
embed_html
HTML embedding code. Deprecation notice:
Former endpoint dailymotion.com/embed has been deprecated.
Learn more about the migration towards new endpoint.
Use the context parameter to specify a Player ID, to use custom Player configuration and ensure optimized monetization.

URL
embed_url
URL to embed this video. Deprecation notice:
Former endpoint dailymotion.com/embed has been deprecated.
Learn more about the migration towards new endpoint.
Use the context parameter to specify a Player ID, to use custom Player configuration and ensure optimized monetization.

NUMBER
encoding_progress
When this video status field is set to processing, this parameter indicates a number between 0 and 100 corresponding to the percentage of encoding already completed. When this value reaches 100, it’s possible for the owner to play his video. For other statuses this parameter returns -1. See also publishing_progress.

DATE
end_time
End date and time of this live stream.

DATE
expiry_date
Date and time after which this video will be made private. Beware: if the video was originally defined as private, setting this value will automatically make it public between its publish_date and expiry_date. This setting only affects the visibility of the video, it will still be available to anyone who knows how to access the video’s private URL even after this date. Omitting this value while setting a past publish_date never expires the video. Set to null (recommended) or a date after Jan 19th 2038 to reset this parameter.

Note : Only verified partners are allowed to manage video availability and expiration dates.

BOOLEAN
expiry_date_availability
By default, videos reaching their expiry_date are still available to anyone who knows how to access their private URL. Set this to false to disable this behavior.

BOOLEAN
expiry_date_deletion
By default, videos are deleted (after a grace period) when their expiry_date is reached. Set this to false to disable this behavior.

Note : Only verified partners are allowed to manage video availability and expiration dates.

BOOLEAN
explicit
True if this video is explicit. Warning: It’s not possible to remove this flag once set.

URL
filmstrip_60_url
URL of the filmstrip sprite of this video. 100 images arranged in a 10×10 grid. Not available for short videos.

URL
first_frame_60_url
URL of this video’s first_frame image (60px height).

URL
first_frame_120_url
URL of this video’s first_frame image (120px height).

URL
first_frame_180_url
URL of this video’s first_frame image (180px height).

URL
first_frame_240_url
URL of this video’s first_frame image (240px height).

URL
first_frame_360_url
URL of this video’s first_frame image (360px height).

URL
first_frame_480_url
URL of this video’s first_frame image (480px height).

URL
first_frame_720_url
URL of this video’s first_frame image (720px height).

URL
first_frame_1080_url
URL of this video’s first_frame image (1080px height).

ARRAY
geoblocking
List of countries where this video is or isn’t accessible. A list of country codes (ISO 3166-1 alpha-2) starting with the deny or allow (default) keyword to define if this is a block or an allowlist, e.g.: both allow, fr, us, it and fr, us, it will allow this video to be accessed in France, US and Italy and deny all other countries. On the other hand, deny, us, fr will deny access to this video in the US and France and allow it everywhere else. An empty list or simply allow (the default) will revert the behavior to allow from everywhere. To set geoblocking on your videos, you have to be a Dailymotion partner.

ARRAY
geoloc
Geolocalization for this video. Result is an array with the longitude and latitude using point notation. Longitude range is from -180.0 (West) to 180.0 (East). Latitude range is from -90.0 (South) to 90.0 (North).

ARRAY
hashtags
List of hashtags attached to this video.

NUMBER
height
Height of this video from the source (px).

IDENTIFIER
id
Unique object identifier (unique among all videos)

BOOLEAN
is_created_for_kids
True if this video is "Created for Kids" (intends to target an audience under the age of 16).

STRING
item_type
Graph type of this object (hopefully video)

STRING
language
Language of this video. This value is declarative and corresponds to the user-declared spoken language of the video. Allowed values are ISO-639-3 alpha-2 and alpha-3 language codes.

DATE
liked_at
Date and time when this video was liked by the user.

NUMBER
likes_total
Total amount of times this video has been liked.

DATE
live_ad_break_end_time
Estimated time for the end of the commercial ad break.

NUMBER
live_ad_break_launch
Launches a given number of ad breaks for this live stream.

NUMBER
live_ad_break_remaining
Returns the number of remaining ad break for this live stream.

DATE
live_airing_time
Date and time when this live stream went on-air for the last time

NUMBER
live_audio_bitrate
Live stream information: audio bitrate (b/s)

BOOLEAN
live_auto_record
True if this live stream is automatically recorded.

STRING
live_backup_video
The live backup video, it is get/set as an xid, but is stored as an integer ID in DB

DICT
live_ingests
List of available live ingests.

URL
live_publish_srt_url
URL to publish the live source stream on using SRT. The current logged-in user needs to own this video to retrieve this field.

URL
live_publish_url
URL to publish the live source stream on. The current logged in user need to own this video in order to retrieve this field.

DICT
log_external_view_urls
A one time usage list of URLs to be called in order log a view on this video made on a

third party site (i.e.: embed player). See the log_view_urls field for format.

URL
log_view_url
A one time usage URL to log a view on this video. This URL expires after a short period of time, thus you should request it at the last moment.

DICT
log_view_urls
A one time usage list of URLs that will be called in order to log video view events.

The format of the dict is a key containing the label of the log URL + some directive on when to call it and the URL as value.
If the app encounters a key format it doesn’t understand, it should skip it with a console warning.
The format of the key is as follows: <label>(@<rule>)?
The label value is a alphanumeric string : [A-Za-z0-9]+
If no @ followed by rules is present, it means the URL has to be called as soon as the video starts (equivalent to label@0).
When the "mode" field of the video object is "live" and any ‘%’ character is found in the rules, the key should be skipped with a console warning.
The rule format is as follows: <delay>([,|]<delay>)*(/<recurrence>)?
The delay value can contain time spent in seconds (## or ##s) or minutes (##m), or in percentage of video duration (##%).
Delays can be separated by comas (all delays apply) or pipes (first match win, others are ignored).
It is not allowed to mix comas and pipes in the same rule. If not specified, default delay should be considered as "0s".
The recurrence value can contain time spent in seconds (## or ##s) or minutes (##m), or in percentage of video duration (##%).
The first recurrent trigger must occur after all the relevant delays have been triggered. It means that delay condition(s) (if valid) have total priority over the recurrence condition (see examples below).

Here are examples of valid keys:

logview : triggered as soon as the video starts.
liked@50%|10m : triggered when the user has spent the equivalent of 50% of the total video duration (time spent by the user = <video duration in seconds> * 0.5) or watched 10 minutes of the video (first match win)
ads@10s,639s : triggered when reaching 10 seconds AND 639 seconds of playback (all delays apply)
progress@10s/30s : triggered when reaching 10 seconds, and then each time the user watch 30 seconds of the video
progress@10s/10% : triggered when reaching 10 seconds, and then each time the user watch the equivalent of 10% of the total video duration (<video duration in seconds> * 0.1)
progress@/20% : triggered as soon as the video starts, and then each time the user watch the equivalent of 20% of the total video duration (<video duration in seconds> * 0.2)

The URL may contain markers that must be replaced by the client:

%session% marker is replaced by a generated UDID stored on the client to identify the users session over several requests. If the app can’t store such id, the URL must be ignored.
%time% marker is replaced by an integer value containing the total time spent in seconds by the client since he has started the video (it is NOT the number of seconds of the player playback position). For example, if the user watch 10 seconds of the video, then seek to 70% of the video and watch 5 additional seconds then stop, %time% is equal to 15 (seconds).
%position% marker is replaced by a float value between 0 and 1 (decimal separator is a point and not a coma and with at least 3 decimals) containing the current position of the player playback in percentage (it may be possible that multiple events are sent with the same position value within a single video view, when a seek occured). When the "mode" field is "live", this value should always be replaced by 0.
STRING
media_type
Media type of this content.

STRING
mode
Stream mode.

BOOLEAN
onair
True if this live stream is broadcasting and watchable in the player.

User
owner
Owner of this video. You can retrieve sub-fields of this user object using the dot-notation (e.g.: owner.id).

BOOLEAN
partner
True if the video is owned by a partner.

STRING
password
If a video is protected by a password, this field contains the password (deprecated, as it now only returns NULL). When setting a value on this field, the video visibility changes to "password protected". Setting it to NULL removes the password protection: the visibility is changed to "public".

BOOLEAN
password_protected
True if this video is password-protected.

Video
player_next_video
A unique video picked by the owner, displayed when video’s playback ends. You can retrieve sub-fields of this video object using the dot-notation (e.g.: player_next_video.id).

ARRAY
player_next_videos
An array of video picked by the owner, displayed when video’s playback ends.

URL
preview_240p_url
URL of this video’s video preview.

URL
preview_360p_url
URL of this video’s video preview.

URL
preview_480p_url
URL of this video’s video preview.

BOOLEAN
private
True if this video is private.

STRING
private_id
The private video id. Null if the authentificated user is not the owner of this video. Although successive calls will generate different ids, a private id generated for a given video will always be valid. Beware that if the video is private and you disclose this private id, your video is no longer private.

DATE
publish_date
Date and time after which this video will be made publicly available. Beware: if the video was originally defined as private, setting this value will automatically make it public after the publish_date. This setting only affects the visibility of the video, it will still be available to anyone who knows how to access the video’s private URL even before this date. Omitting this value while setting a future expiry_date immediately publishes the video. Set to null (recommended) or a date before Jan 1st 1990 to reset this parameter.

Note : Only verified partners are allowed to manage video availability and expiration dates.

BOOLEAN
publish_date_keep_private
Keep this video private when its publication_date is reached.

BOOLEAN
published
True if this video is published (may still be waiting for encoding, see the status field for more information).

NUMBER
publishing_progress
When this video status field is set to processing, this parameter indicates a number between 0 and 100 corresponding to the percentage of progress from the status waiting to ready. Unlike encoding_progress that can reach 100 well before the switch from processing to ready, this value will not.

DATE
record_end_time
Date and time when the video record was stopped.

DATE
record_start_time
Date and time when the video record started.

STRING
record_status
Current state of the recording process of this video.

starting: Recording video is going to start
started: Recording video is in progress
stopping: Recording video is going to stop
stopped: Recording video is stopped
STRING
recurrence
Recurrence of this live stream.

URL
seeker_url
URL of the image-based seeker resource of this video. internal resource format is proprietary. Not available for short videos.

STRING
soundtrack_isrc
The International Standard Recording Code of the soundtrack associated to this video.

NUMBER
soundtrack_popularity
Soundtrack popularity.

URL
sprite_320x_url
URL of the sprite of this video, width:320px

URL
sprite_url
URL of the sprite of this video.

DATE
start_time
Start date and time of this live stream.

STRING
status
Status of this video. A video requires the published status to be set to true to be watchable.

BOOLEAN
stream_altered_with_ai
Whether the video stream has been altered by AI

URL
stream_audio_url
URL of this audio stream. Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_h264_hd1080_url
URL of the Full HD video stream (1080p, ~6.25 Mbps). Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_h264_hd_url
URL of the high definition video stream (720p, ~2.17 Mbps). Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_h264_hq_url
URL of the high quality WVGA video stream (480p, ~845 kbps). Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_h264_l1_url
URL of the very low quality/low bandwidth mobile video stream (144p, ~60 kbps). Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_h264_l2_url
URL of the very low quality/high bandwidth mobile video stream (144p, ~106 kbps). Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_h264_ld_url
URL of the low quality QVGA Mobile 3G video stream (240p, ~260 kbps). Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_h264_qhd_url
URL of the Quad HD video stream (1440p, ~10.4 Mbps). Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_h264_uhd_url
URL of the Ultra HD 4K video stream (2160p, ~16.5 Mbps). Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_h264_url
URL of the medium quality video stream (384p, ~465 kbps). Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_hls_url
URL of the adaptative bitrate manifest using the Apple HTTP Live Streaming protocol. Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_live_hls_url
URL of this live stream using the HTTP Live Streaming protocol. Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_live_rtmp_url
URL of this live stream using the RTMP protocol. Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_live_smooth_url
URL of this live stream using the Smooth Streaming protocol. Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
stream_source_url
URL of this video source. Without an access token this field contains null, the dailymotion user associated with the access token must be the owner of the video. This field returns null a few days after the video upload. Please refer to others stream_*_url fields to get a stream. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

BOOLEAN
studio
True if this video is produced by the Dailymotion studio.

ARRAY
tags
List of tags attached to this video.

URL
thumbnail_60_url
URL of this video’s thumbnail image (60px height).

URL
thumbnail_62_url
URL of this video’s thumbnail image (62px height).

URL
thumbnail_120_url
URL of this video’s thumbnail image (120px height).

URL
thumbnail_180_url
URL of this video’s thumbnail image (180px height).

URL
thumbnail_240_url
URL of this video’s thumbnail image (240px height).

URL
thumbnail_360_url
URL of this video’s thumbnail image (360px height).

URL
thumbnail_480_url
URL of this video’s thumbnail image (480px height).

URL
thumbnail_720_url
URL of this video’s thumbnail image (720px height).

URL
thumbnail_1080_url
URL of this video’s thumbnail image (1080px height).

URL
thumbnail_url
URL of this video’s raw thumbnail (full size respecting ratio). Some users have the permission to change this value by providing an URL to a custom thumbnail. If you don’t have the permission, the thumbnail won’t be updated. Note: for live streams, the thumbnail is automatically generated every 5 mn by default; it is not possible anymore to manually refresh the preview. Maximum allowed file size is 10MB

URL
tiny_url
Tiny URL of this video.

STRING
title
Title of this video.

DATE
updated_time
Date and time when this video was last updated.

DATE
uploaded_time
Date and time when this video was originally uploaded.

URL
url
URL of this video on Dailymotion. Writing this parameter defines where to download the video source. You may either use this parameter at video creation time or change this parameter later if you want to change this video source afterward. To change an existing video, the authenticated user may need some additional permissions. You may use the GET /file/upload API resource to upload a video file and create a URL to provide to this method or use an existing URL pointing to your own video file. Writing to this parameter is subject to rate limiting.

BOOLEAN
verified
True if the video is owned by a verified partner.

NUMBER
views_last_day
Total number of views on this video in the last 24 sliding hours.

NUMBER
views_last_hour
Total number of views on this video in the last sliding hour.

NUMBER
views_last_month
Total number of views on this video in the last 30 sliding days.

NUMBER
views_last_week
Total number of views on this video in the last 7 sliding days.

NUMBER
views_total
Total amount of views on this video since its publication.

NUMBER
width
Width of this video from the source (px).

Video deprecated fields
These deprecated fields were once part of the API reference but are no longer maintained. Support is still available until the end of life date specified for each field. Do not use any of these for a new project as they may disappear without warning.

Expand all
Collapse all
BOOLEAN
 3d
True if this video is in 3D format.

BOOLEAN
 adfit
True if advertising id allowed on this video depending on its content.

BOOLEAN
 allowed_in_groups
True if this video can be added to groups.

NUMBER
 bookmarks_total
Total amount of times this video has been added to a user’s favorites.

BOOLEAN
 broadcasting
True if this live stream is ready for delivery.

STRING
 duration_formatted
Duration of this video (human readable).

DATE
 favorited_at
Date and time when this video was bookmarked by the current user.

URL
 filmstrip_small_url
Sprite URL of snapshots of this video if it exists.

STRING
 isrc
Detected ISRC (International Standard Recording Code) of the soundtrack.

BOOLEAN
 live_broadcasting
False if this live stream is only visible by his owner.

URL
 log_external_view_url
One time usage URL to log a view on this video made on a third party site (i.e.: embedded player). This URL expires after a short period of time, thus you should request it at the last moment.

DATE
 modified_time
Date and time when this video was last modified.

STRING
 muyap
Detected MUYAP (Turkish Phonographic Industry Society Identifier) of the soundtrack.

URL
 owner_avatar_large_url
URL of the avatar image of the owner of this video (160px by 160px).

URL
 owner_avatar_medium_url
URL of the avatar image of the owner of this video (80px by 80px).

URL
 owner_avatar_small_url
URL of the avatar image of the owner of this video (40px by 40px).

STRING
 owner_fullname
Full name of the owner of this video.

STRING
 owner_screenname
Username or fullname of the owner of this video, depending on user preference.

URL
 owner_url
URL of the owner of this video.

STRING
 owner_username
Username of the owner of this video.

STRING
 provider_id
Content provider identifier.

NUMBER
 rating
Average number of stars this video has received as a float.

NUMBER
 ratings_total
Total amount of users who voted for this video.

STRING
 rental_price
Price of renting this video as a float in the current currency or null if this video is not behind a paywall. See the currency field of the /locale endpoint to retrieve the current currency.

STRING
 rental_price_formatted
Price of renting this video, formatted with currency according to the request localization. Will be null if this video is not behind a paywall.

URL
 stream_chromecast_url
URL of the video stream for Chromecast devices :

The returned URL is HTTPS only
&max=1080 is appended to the returned URL because Chromecast does not support qualities above 1080
URL
 stream_live_hls_source_url
URL of this live stream source using the HTTP Live Streaming protocol. Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

URL
 stream_ljhs_url
URL of the adaptative bitrate manifest using the Dailymotion LumberJack Streaming protocol. Without an access token this field contains null, the Dailymotion user associated with the access token must be the owner of the video. This field is rate limited. The returned url is secured: it can only be consumed by the user who made the query and it expires after a certain time.

ARRAY
 strongtags
List of strong tags attached to this video.

URL
 swf_url
URL of the legacy SWF embed player (only use this to embed the player into a flash movie, otherwise use embed_url).

URL
 thumbnail_large_url
URL of this video thumbnail image (320px by 240px).

URL
 thumbnail_medium_url
URL of this video thumbnail image (160px by 120px).

URL
 thumbnail_small_url
URL of this video thumbnail image (80px by 60px).

STRING
 type
Content type of this video (can be official, creative or null).

STRING
 upc
Detected UPC (Universal Product Code) of the soundtrack.

STRING
 vast_url_template
VAST template URL as a string for this video or null if video doesn’t accept in-stream ads.

Video filters
Here is the list of filters you can use to limit a result set of video objects. You can use these by passing them as query-string parameters with your request.

Expand all
Collapse all
360_degree
Limit the result set to 360 videos.

advertising_instream_blocked
Limit the result set to advertising_instream_blocked

allowed_in_playlists
Limit the results to videos which are allowed in playlists.

availability
Limit the result set to available videos.

channel
Limit the result set to this channel.

country
Limit the result set to this country (declarative).

created_after
Limit the result set to videos created after this date and time.

created_before
Limit the result set to videos created before this date and time.

exclude_channel_ids
List of channels ids to exclude from the result set.

exclude_ids
List of video ids to exclude from the result set.

explicit
Limit the result set to the provided explicit value for videos.

exportable
Limit the result set to exportable (i.e: no-export flag not set) videos.

featured
Limit the result set to featured videos.

flags
List of simple boolean flags available to reduce the result set.

has_game
Limit the result set to videos related to a video-game.

hd
Limit the result set to high definition videos (vertical resolution greater than or equal to 720p).

ids
Limit the result set to this list of video identifiers (works only with xids).

in_history
Limit the result set to videos in your watch history.

is_created_for_kids
Limit the result set to the provided is_created_for_kids value for videos.

languages
Limit the result set to this list of languages. Language is declarative and corresponds to the user-declared spoken language of the video. If you wish to retrieve content currated for a specific locale, use the localization global parameter instead.

list
Limit the result set to this video list. Warning: Can not be combined with a search.

live
Limit the result set to live streaming videos.

live_offair
Limit the result set to off-air live streaming videos.

live_onair
Limit the result set to on-air live streaming videos.

live_upcoming
Limit the result set to upcoming live streaming videos.

longer_than
Limit the results to videos with a duration longer than or equal to the specified number of minutes.

mode
Limit the result set to videos of this mode.

no_live
Limit the result set to non-live streaming videos.

no_live_recording
Limit the result set to live recording videos.

no_premium
Limit the result set to free video content.

nogenre
Limit the result set by excluding this genre.

owners
Limit the result set to this list of user identifiers or logins.

partner
Limit the result set to partner videos.

password_protected
Limit the result set to password protected partner videos.

premium
Limit the result set to premium SVOD and TVOD video content.

private
Limit the result set to private videos.

related_videos_algorithm
Forces the recommendation result to use a specifc algorithm

search
Limit the result set to this full text search.

shorter_than
Limit the results to videos with a duration shorter than or equal to the specified number of minutes.

sort
Change the default result set ordering. Notes:

the relevance filter can only be used in conjunction with the search filter.
Deprecated sorts (ranking, rated, rated-hour, rated-today, rated-week, rated-month, commented, commented-hour, commented-today, commented-week, commented-month)
tags
Limit the result set to this full text search of video tags. By default perform ‘AND’ operation between terms. Use enclosing parenthesis ‘()’ on the query to perform ‘OR’ operation.

timeframe
Limit the result set to videos created after this N last seconds.

ugc
Limit the result set to user generated video content (no partner content).

ugc_partner
Limit the result set to user generated or partner video content.

unpublished
Limit the result set to unpublished videos.

verified
Limit the result set to verified partner videos.

Video deprecated filters
These deprecated filters were once part of the API reference but are no longer maintained. Support is still available until the end of life date specified for each filter. Do not use any of these for a new project as they may disappear without warning.

Expand all
Collapse all
 3d
Limit the result set to 3D videos.

 filters
List of simple boolean filters available to reduce the result set.

 language
Limit the result set to this language. This value is declarative and corresponds to the user-declared spoken language of the video. If you wish to retrieve content currated for a specific locale, use the localization global parameter instead.

 modified_after
Limit the result set to videos updated after this date and time.

 modified_before
Limit the result set to videos updated before this date and time.

 owner
Limit the result set to videos of this user.

 strongtags
Limit the result set to this strong tag.

Video connections
Connections through the data API are used to link objects with each others. Some objects can only be accessed and/or created through connections since they have no point in existing on their own. Here is the list of connections available through the video object.

Expand all
Collapse all
[Video]
recordings
List of videos recorded from this video live.
This connection joins an object of type video with a list of video objects.

[Video]
related
List of videos related to this video.
This connection joins an object of type video with a list of video objects.

[Subtitle]
subtitles
List of subtitles available for this video.
This connection joins an object of type video with a list of subtitle objects.

Changelog
embed_html and embed_url returning new embed endpoint
Date: 2024-09-23

As part of the progressive deprecation of the legacy embed endpoint, the API fields embed_html and embed_url are now returning the new embed endpoint.

Learn more about the deprecation of the legacy embed endpoint and how to update your integration if you’re using one of these two API fields:

Update embed_html
Update embed_url
Pass Player ID with embed_url and embed_html
Date: 2023-10-09

You should now pass your Player ID in the embed_url and embed_html fields by adding context=player%3D{PlayerID} in your request.
This ensures you can benefit from custom Player settings, accurate tracking and centralized management in your Dailymotion Studio.

Request example: 
https://api.dailymotion.com/video/x8mubmn?fields=embed_html,embed_url&context=player%3Dxc394

Answer example: "embed_url": "https://geo.dailymotion.com/player/xc394.html?video=x8mubmn"

Note: This method uses the new embed endpoint geo.dailymotion.com.
Former endpoint dailymotion.com/embed will soon be deprecated.

Player field for Google compliance
Date: 2023-03-03

If you rely on Google advertisement, you can set our new Player field 
enable_google_policy_ui
 to true to use our Google compliant PiP interface (with the close button outside PiP) to keep generating revenue from it.

Errore type DM019
Date: 2022-04-07

New error type (DM019) exposed on the Player for the content uploaded by inactive users

Your privacy settings
Dailymotion sets tracking tools (cookies) on your device, either directly or via its service providers to analyze user behavior on this website and further promote Dailymotion’s services to you. By clicking the “Accept All” button, you consent to the use of non-essential cookies, our processing of the personal data collected by us and its share with our Affiliates. Refusing to consent does not prevent you from accessing this website, and you can review or change your preferences via the “Personalize” button or, at any time, on the “Consent Management” link of our Dailymotion for Developers website. Learn more about our Privacy Policy.

Refuse All
Personalize
Accept All
Consent Management
Cookies are small files dropped on your device when you browse on this Dailymotion for Developers website.

We use essential cookies which are necessary for the operation of our website and help protect you against security risks. These cookies allow our service to operate properly and do not require your consent.

Additionally, we use non-essential cookies to better understand your use of our website and services in order to improve and develop them. The non-essential cookies we use may be either developed by us or by our service providers.
The use of non-essential cookies is subject to your consent.

You can, at any time, personalize and manage which non-essential cookies go to your browser. Your consent preferences only apply to the browser and device you are currently using.
You can see the list of cookies used by Dailymotion including the cookies used on this website for audience measurement purposes by clicking here.

We may share the collected data with our Affiliates, meaning with wholly owned subsidiaries of Vivendi SE. Subject to your consent, these Affiliates may share your personal data with us.

Refuse All Purposes
Accept All Purposes
Essential cookies
Audience Measurement Purpose
Sharing of Personal Data with Affilates
Confirm selection

COMPANY
About
Press
News
Our Story
Dailymotion.com
