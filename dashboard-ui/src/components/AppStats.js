// import React, { useEffect, useState } from 'react'
// import '../App.css';

// export default function AppStats() {
//     const [isLoaded, setIsLoaded] = useState(false);
//     const [stats, setStats] = useState({});
//     const [error, setError] = useState(null)

// 	const getStats = () => {
	
//         fetch(`http://fzhukafka.westus3.cloudapp.azure.com/stats:8100`)
//             .then(res => res.json())
//             .then((result)=>{
// 				console.log("Received Stats")
//                 setStats(result);
//                 setIsLoaded(true);
//             },(error) =>{
//                 setError(error)
//                 setIsLoaded(true);
//             })
//     }
//     useEffect(() => {
// 		const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
// 		return() => clearInterval(interval);
//     }, [getStats]);

//     if (error){
//         return (<div className={"error"}>Error found when fetching from API</div>)
//     } else if (isLoaded === false){
//         return(<div>Loading...</div>)
//     } else if (isLoaded === true){
//         return(
//             <div>
//                 <h1>Latest Stats</h1>
//                 <table className={"StatsTable"}>
// 					<tbody>
// 						<tr>
// 							<th>Inventory Added</th>
// 							<th>Updated Inventory</th>
// 						</tr>
// 						<tr>
// 							<td># Inventory: {stats['Quantity']}</td>
// 							<td># Updated: {stats['last_updated']}</td>
// 						</tr>
// 						<tr>
// 							<td colspan="2">Location of inventory: {stats['location']}</td>
// 						</tr>
// 						<tr>
// 							<td colspan="2">Item Name: {stats['name']}</td>
// 						</tr>
// 						<tr>
// 							<td colspan="2">Item ID: {stats['id']}</td>
// 						</tr>
// 					</tbody>
//                 </table>
//                 <h3>Last Updated: {stats['last_updated']}</h3>

//             </div>
//         )
//     }
// }

import React, { useEffect, useState, useCallback } from 'react';
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null);

    const getStats = useCallback(() => {
        fetch(`http://fzhukafka.westus3.cloudapp.azure.com:8100/inventory`)
            .then(res => res.json())
            .then(
                (result) => {
                    console.log("Received Stats");
                    setStats(result);
                    setIsLoaded(true);
                },
                (error) => {
                    setError(error);
                    setIsLoaded(true);
                }
            );
    }, []); // Dependencies array is empty because getStats does not depend on any external values

    useEffect(() => {
        const interval = setInterval(getStats, 2000); // No need for arrow function here
        return () => clearInterval(interval);
    }, [getStats]);
    

    if (error) {
        return (<div className={"error"}>Error found when fetching from API</div>);
    } else if (!isLoaded) {
        return (<div>Loading...</div>);
    } else {
        return (
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
                    <tbody>
                        <tr>
                            <th>Inventory Added</th>
                            <th>Updated Inventory</th>
                        </tr>
                        <tr>
                            <td># Inventory: {stats['Quantity']}</td>
                            <td># Updated: {stats['last_updated']}</td>
                        </tr>
                        <tr>
                            <td colSpan="2">Number of inventory: {stats['num_inventories']}</td>
                        </tr>
                        <tr>
                            <td colSpan="2">Number of updates: {stats['num_updates']}</td>
                        </tr>
                        <tr>
                            <td colSpan="2">Item ID: {stats['id']}</td>
                        </tr>
                    </tbody>
                </table>
                <h3>Last Updated: {stats['last_updated']}</h3>
            </div>
        );
    }
}

