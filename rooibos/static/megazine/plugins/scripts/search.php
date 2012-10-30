<?php
/*
 * MegaZine3 - Pageflip Engine
 *
 * Copyright (c) 2009-2010, VservU GmbH (Florian Nuecke and Hans J. Nuecke)
 *
 * The following terms define a license agreement between you and VservU GmbH,
 * which you accept by using MegaZine3 (the Software).
 *
 * This license agreement grants you the right to use the Software on any
 * number of devices, and is valid for private use for an unlimited amount of
 * time.
 *
 * A commercial license can be purchased; please contact mz3-info@vservu.de for
 * details. When purchasing a commercial license, its terms substitute this
 * license agreement.
 *
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 *   * Redistributions of source code must retain the above copyright and
 *     license notice, this list of conditions and the following disclaimer.
 *
 *   * Redistributions in binary form must reproduce the above copyright
 *     notice and license, this list of conditions and the following disclaimer
 *     in the documentation and/or other materials provided with the
 *     distribution.
 *
 *   * Neither the name of VservU GmbH nor the names of its contributors may be
 *     used to endorse or promote products derived from this software without
 *     specific prior written permission.
 *
 *
 * This software is provided by the copyright holders and contributors "AS IS"
 * and any express or implied warranties, including, but not limited to, the
 * implied warranties of merchantability and fitness for a particular purpose
 * are disclaimed.
 *
 * IN NO EVENT shall the copyright owner or contributors be liable for any
 * direct, indirect, incidental, special, exemplary, or consequential damages
 * (including, but not limited to, procurement of substitute goods or services;
 * loss of use, data, or profits; or business interruption) however caused and
 * on any theory of liability, whether in contract, strict liability, or tort
 * (including negligence or otherwise) arising in any way out of the use of
 * this software, even if advised of the possibility of such damage.
 */

function sort_by_count($a, $b) {
	return $a["count"] < $b["count"];
}

header('Content-Type: text/xml; charset=utf-8');
echo '<?xml version="1.0" encoding="utf-8"?>' . "\n";
if (array_key_exists("cat", $_REQUEST) && $_REQUEST["cat"]) {
	// Get category name.
	$category = $_REQUEST["cat"];
	
	// Do not allow directory traversal upwards!
	if (substr($category, 0, 3) != "../" && strstr($category, "/../") === FALSE) {
		if (array_key_exists("q", $_REQUEST) && $_REQUEST["q"]) {
			// Search request given. Load the index for the given category.
			$rawdata = @file_get_contents("index/" . $category . ".txt");
			if ($rawdata !== FALSE) {
				// Prepare the query by splitting it up and checking for
				// required and forbidden words.
				$forbidden = array(); // words prefixed with a "-"
				$required  = array(); // words prefixed with a "+"
				$optional  = array(); // normal words
				
				// Get abd format query.
				$query = $_REQUEST["q"];
				
				// Split it up.
				$query_parts = explode(" ", $query);
				
				// Check the parts.
				foreach ($query_parts as $query_part) {
					$query_part = trim($query_part);
					if (!$query_part) {
						continue;
					}
					switch ($query_part[0]) {
						case '-':
							// Forbidden.
							if (strlen($query_part) > 1) {
								$forbidden[] = substr($query_part, 1);
							}
							break;
						case '+':
							// Required.
							if (strlen($query_part) > 1) {
								$required[] = substr($query_part, 1);
							}
							break;
						default:
							// Optional.
							$optional[] = $query_part;
					}
				}
				
				if (count($required) || count($optional) || count($forbidden)) {
					// Begin actual search. Check for wanted excerptlength.
					$excerptlen = array_key_exists("excerptlen", $_REQUEST)
							? (int)$_REQUEST["excerptlen"] / 2
							: 30;
					
					// Split it up at the page break mark to get one entry per page.
					$pages = explode("\f", $rawdata);
					
					// Results.
					$results = array();
					
					// Check all pages.
					for ($i = 0; $i < count($pages); ++$i) {
						// Page content.
						$page = $pages[$i];
						// Reset result.
						$result = array("page" => ($i + 1),
										"excerpt" => "",
										"count" => 0);
						
						// If there are forbidden key words search for them.
						foreach ($forbidden as $word) {
							if (stripos($page, $word) !== FALSE) {
								// Forbidden word found, skip page.
								continue 2;
							}
						}
						
						// If there are required key words search for them.
						foreach ($required as $word) {
							$offset = -1;
							$found = false;
							while (($offset = stripos($page, $word, $offset + 1)) !== FALSE) {
								$found = true;
								if (!$result["excerpt"]) {
									$result["excerpt"] = substr($page,
											   max(0, $offset - $excerptlen),
											   $offset + $excerptlen + count($word));
								}
								++$result["count"];
							}
							if (!$found) {
								// One required word not found, skip page.
								continue 2;
							}
						}
						
						// If there are optional key words search for them.
						foreach ($optional as $word) {
							$offset = -1;
							while (($offset = stripos($page, $word, $offset + 1)) !== FALSE) {
								if (!$result["excerpt"]) {
									$result["excerpt"] = substr($page,
											   max(0, $offset - $excerptlen),
											   $offset + $excerptlen + count($word));
								}
								++$result["count"];
							}
						}
						
						// If there were matches store result.
						if ($result["count"]) {
							$results[] = $result;
						}
					}
					
					// Sort results by number of matches on the page.
					usort($results, "sort_by_count");
					
					// Print results.
					echo "<search status=\"ok\">";
					foreach ($results as $result) {
						echo "\t<result page=\"" . $result["page"] . "\" matches=\"" . $result["count"] . "\">\n";
						echo "\t\t<![CDATA[..." . $result["excerpt"] . "...]]>\n";
						echo "\t</result>\n";
					}
					echo "</search>";
				} else {
					// Empty query.
					//echo "<search status=\"error\" message=\"Empty query.\">\n";
					echo "<search status=\"ok\"/>";
				}
			} else {
				echo "<search status=\"error\" message=\"Index for given category could not be found or opened.\"/>";
			}
		} else {
			echo "<search status=\"error\" message=\"No query given (query variable 'q').\"/>";
		}
	} else {
		echo "<search status=\"error\" message=\"Invalid category string given (tried upward directory traversal).\"/>";
	}
} else {
	echo "<search status=\"error\" message=\"No category given (query variable 'cat').\"/>";
}
?>