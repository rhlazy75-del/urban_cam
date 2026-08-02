import React from "react";

export default function Loader({ loading }) {
    return (
        <div className={`loader ${!loading ? "loader-hide" : ""}`}>
            <div className="loader-content">
                <div className="loader-logo">Urban visual pollution</div>
                <div className="loader-chart-wrap">
                    <svg className="loader-chart" viewBox="0 0 300 90">
                        <path
                            id="loaderLine"
                            className="loader-chart-path"
                            d="M0,66 C24,66 30,78 46,78 C64,78 66,50 88,50 C108,50 112,68 132,68 C154,68 158,20 190,18 C216,16 224,30 246,30 C266,30 272,10 296,8"
                        />
                        <circle r="4.5" fill="#f2a93b" className="loader-chart-dot">
                            <animateMotion dur="2.2s" fill="freeze" calcMode="linear" keyPoints="0;1" keyTimes="0;1">
                                <mpath xlinkHref="#loaderLine" />
                            </animateMotion>
                        </circle>
                    </svg>
                </div>
                <div className="loader-caption">Loading city view</div>
            </div>
        </div>
    );
}